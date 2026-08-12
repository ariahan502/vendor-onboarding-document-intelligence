"""Run deterministic regression checks for the vendor onboarding MVP.

The suite creates an isolated SQLite database and temporary PDFs, so it never changes
the local development queue. It intentionally leaves Azure OCR unconfigured to verify the
safe manual-review fallback for scanned documents.
"""

import os
import tempfile
from pathlib import Path


def build_pdf(text: str) -> bytes:
    """Create a minimal text PDF without adding a test-only dependency."""
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, content in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_id} 0 obj\n".encode())
        output.extend(content)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(output)


SCENARIOS = [
    {
        "name": "missing_insurance",
        "documents": {
            "contract": "Vendor: Acme Vendor LLC  Payment Terms: Net 30",
            "w9": "Legal Name: Acme Vendor LLC  EIN: 12-3456789",
        },
        "expected_titles": ["Missing required insurance certificate"],
    },
    {
        "name": "name_mismatch",
        "documents": {
            "contract": "Vendor: Acme Vendor LLC  Payment Terms: Net 45",
            "w9": "Legal Name: Acme Vendor Incorporated  EIN: 12-3456789",
            "insurance_certificate": "Coverage: $1,000,000",
        },
        "expected_titles": ["Vendor legal name differs between contract and W-9"],
    },
    {
        "name": "tax_id_gap",
        "documents": {
            "contract": "Vendor: Acme Vendor LLC  Payment Terms: Net 30",
            "w9": "Legal Name: Acme Vendor LLC",
            "insurance_certificate": "Coverage: $1,000,000",
        },
        "expected_titles": ["Tax ID could not be extracted from uploaded W-9"],
    },
    {
        "name": "scanned_w9_needs_ocr",
        "documents": {"w9": ""},
        "expected_titles": ["OCR required for uploaded w9"],
    },
]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="vendor-onboarding-eval-") as temp_dir:
        temp_path = Path(temp_dir)
        os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{temp_path / 'evaluation.db'}"
        os.environ["UPLOAD_DIR"] = str(temp_path / "uploads")
        os.environ.pop("DOCUMENT_INTELLIGENCE_ENDPOINT", None)
        os.environ.pop("DOCUMENT_INTELLIGENCE_API_KEY", None)

        from fastapi.testclient import TestClient

        from app.db.base_metadata import Base
        from app.db.session import SessionLocal, engine
        from app.main import app
        from app.services.package_service import process_next_queued_package

        Base.metadata.create_all(bind=engine)
        client = TestClient(app)
        client.headers.update(
            {"X-Actor-ID": "evaluation.runner", "X-Actor-Role": "admin"}
        )
        failures: list[str] = []

        for scenario in SCENARIOS:
            package = client.post(
                "/api/packages/",
                json={
                    "vendor_name": "Acme Vendor LLC",
                    "tax_id": None,
                    "country": "US",
                    "category": "consulting",
                    "assigned_reviewer": "evaluation.runner",
                    "submitted_documents": [
                        {"doc_type": doc_type, "file_name": f"{doc_type}.pdf"}
                        for doc_type in scenario["documents"]
                    ],
                },
            )
            package.raise_for_status()
            package_id = package.json()["package_id"]

            for doc_type, text in scenario["documents"].items():
                response = client.post(
                    f"/api/packages/{package_id}/documents",
                    data={"doc_type": doc_type},
                    files={"file": (f"{doc_type}.pdf", build_pdf(text), "application/pdf")},
                )
                response.raise_for_status()
                downloaded = client.get(
                    f"/api/packages/{package_id}/documents/{response.json()['document_id']}/file"
                )
                download_passed = downloaded.status_code == 200 and downloaded.content == build_pdf(text)
                if not download_passed:
                    failures.append(f"{scenario['name']} document download failed through storage boundary")

            processed = client.post(f"/api/packages/{package_id}/simulate-processing")
            processed.raise_for_status()
            detail = client.get(f"/api/packages/{package_id}")
            detail.raise_for_status()
            titles = [finding["title"] for finding in detail.json()["findings"]]
            missing_titles = [
                title for title in scenario["expected_titles"] if title not in titles
            ]
            status = "PASS" if not missing_titles else "FAIL"
            print(f"{status} {scenario['name']}: {', '.join(titles)}")
            if missing_titles:
                failures.append(f"{scenario['name']} missing: {', '.join(missing_titles)}")

            if scenario["name"] == "missing_insurance":
                denied = client.post(
                    f"/api/packages/{package_id}/decisions",
                    json={
                        "reviewer": "evaluation.runner",
                        "final_decision": "approve",
                        "reviewer_comment": "Attempting approval without override.",
                        "override_reason": None,
                    },
                )
                allowed = client.post(
                    f"/api/packages/{package_id}/decisions",
                    json={
                        "reviewer": "evaluation.runner",
                        "final_decision": "approve",
                        "reviewer_comment": "Document was independently verified.",
                        "override_reason": "Insurance evidence was independently verified.",
                    },
                )
                approval_guard_passed = denied.status_code == 422 and allowed.status_code == 200
                print("PASS approval_override_guard" if approval_guard_passed else "FAIL approval_override_guard")
                if not approval_guard_passed:
                    failures.append("approval_override_guard did not enforce an override reason")

                insurance_finding = next(
                    finding
                    for finding in detail.json()["findings"]
                    if finding["title"] == "Missing required insurance certificate"
                )
                resolution = client.post(
                    f"/api/packages/{package_id}/finding-resolutions",
                    json={
                        "finding_id": insurance_finding["finding_id"],
                        "reviewer": "evaluation.runner",
                        "resolution_status": "accepted_risk",
                        "resolution_note": "Coverage exception was approved outside the workflow.",
                    },
                )
                resolved_detail = client.get(f"/api/packages/{package_id}")
                resolved_detail.raise_for_status()
                resolution_state = next(
                    finding
                    for finding in resolved_detail.json()["findings"]
                    if finding["finding_id"] == insurance_finding["finding_id"]
                )
                approved_after_resolution = client.post(
                    f"/api/packages/{package_id}/decisions",
                    json={
                        "reviewer": "evaluation.runner",
                        "final_decision": "approve",
                        "reviewer_comment": "Accepted risk has been documented.",
                        "override_reason": None,
                    },
                )
                resolution_passed = (
                    resolution.status_code == 200
                    and resolution_state["finding_status"] == "accepted_risk"
                    and approved_after_resolution.status_code == 200
                )
                print("PASS finding_resolution_lifecycle" if resolution_passed else "FAIL finding_resolution_lifecycle")
                if not resolution_passed:
                    failures.append("finding_resolution_lifecycle did not update approval behavior")

            if scenario["name"] == "name_mismatch":
                field = detail.json()["extracted_fields"][0]
                correction = client.post(
                    f"/api/packages/{package_id}/field-overrides",
                    json={
                        "field_id": field["field_id"],
                        "reviewer": "evaluation.runner",
                        "corrected_value": "Acme Vendor LLC (verified)",
                        "correction_reason": "Verified against the signed contract.",
                    },
                )
                correction.raise_for_status()
                corrected_detail = client.get(f"/api/packages/{package_id}")
                corrected_detail.raise_for_status()
                overrides = corrected_detail.json()["field_overrides"]
                correction_passed = (
                    overrides
                    and overrides[0]["field_id"] == field["field_id"]
                    and overrides[0]["original_value"] == field["raw_value"]
                )
                print(
                    "PASS field_correction_audit"
                    if correction_passed
                    else "FAIL field_correction_audit"
                )
                if not correction_passed:
                    failures.append("field_correction_audit did not preserve original value")

        queued = client.post(
            "/api/packages/",
            json={
                "vendor_name": "Queued Worker Test LLC",
                "tax_id": None,
                "country": "US",
                "category": "consulting",
                "assigned_reviewer": "evaluation.runner",
                "submitted_documents": [],
            },
        )
        queued.raise_for_status()
        queued_id = queued.json()["package_id"]
        db = SessionLocal()
        try:
            worker_result = process_next_queued_package(db)
        finally:
            db.close()
        queued_detail = client.get(f"/api/packages/{queued_id}")
        queued_detail.raise_for_status()
        worker_passed = (
            worker_result is not None
            and worker_result.package_id == queued_id
            and queued_detail.json()["package_status"] == "ready_for_review"
        )
        print("PASS queued_worker_boundary" if worker_passed else "FAIL queued_worker_boundary")
        if not worker_passed:
            failures.append("queued_worker_boundary did not process the queued packet")

        client.headers.update({"X-Actor-ID": "intake.runner", "X-Actor-Role": "intake"})
        role_denied = client.post(
            f"/api/packages/{queued_id}/decisions",
            json={
                "reviewer": "spoofed.actor",
                "final_decision": "approve",
                "reviewer_comment": "Intake must not decide.",
            },
        )
        intake_export_denied = client.get("/api/audit-events/export")
        role_guard_passed = (
            role_denied.status_code == 403 and intake_export_denied.status_code == 403
        )
        print("PASS role_guards" if role_guard_passed else "FAIL role_guards")
        if not role_guard_passed:
            failures.append("role_guards did not reject unprivileged decision or audit export")

        client.headers.update({"X-Actor-ID": "audit.admin", "X-Actor-Role": "admin"})
        policy_catalogue = client.get("/api/policy-rules/")
        policy_catalogue.raise_for_status()
        policy_catalogue_passed = len(policy_catalogue.json()["rules"]) >= 4
        print("PASS policy_catalogue" if policy_catalogue_passed else "FAIL policy_catalogue")
        if not policy_catalogue_passed:
            failures.append("policy_catalogue did not expose the baseline rules")

        policy_rule = policy_catalogue.json()["rules"][0]
        policy_revision = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions",
            json={
                "proposed_expression": "contract, W-9, and insurance certificate are required",
                "proposed_severity": "high",
                "change_reason": "Clarify the document requirement wording.",
            },
        )
        policy_revision.raise_for_status()
        revision_id = policy_revision.json()["revision_id"]
        premature_activation = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions/{revision_id}/activate"
        )
        rejected_evaluation = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions/{revision_id}/evaluate",
            json={
                "case_name": "policy regression failure",
                "extraction_score": 1,
                "finding_score": 0.9,
                "routing_score": 1,
                "reviewer_agreement_score": 1,
            },
        )
        rejected_activation = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions/{revision_id}/activate"
        )
        passing_revision = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions",
            json={
                "proposed_expression": "contract, W-9, and insurance certificate must be present",
                "proposed_severity": "high",
                "change_reason": "Confirm the original requirement after regression evaluation.",
            },
        )
        passing_revision.raise_for_status()
        passing_revision_id = passing_revision.json()["revision_id"]
        passing_evaluation = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions/{passing_revision_id}/evaluate",
            json={
                "case_name": "policy regression pass",
                "case_slice": "required_documents",
                "extraction_score": 1,
                "finding_score": 1,
                "routing_score": 1,
                "reviewer_agreement_score": 1,
            },
        )
        activation = client.post(
            f"/api/policy-rules/{policy_rule['rule_id']}/revisions/{passing_revision_id}/activate"
        )
        revision_list = client.get(f"/api/policy-rules/{policy_rule['rule_id']}/revisions")
        revision_guard_passed = (
            premature_activation.status_code == 422
            and rejected_evaluation.status_code == 200
            and rejected_evaluation.json()["status"] == "rejected"
            and rejected_activation.status_code == 422
            and passing_evaluation.status_code == 200
            and passing_evaluation.json()["status"] == "evaluated"
            and activation.status_code == 200
            and activation.json()["rule_version"] == "policy-v2"
            and revision_list.status_code == 200
            and len(revision_list.json()["revisions"]) == 2
        )
        print("PASS policy_revision_guard" if revision_guard_passed else "FAIL policy_revision_guard")
        if not revision_guard_passed:
            failures.append("policy_revision_guard allowed an untested rule to activate")

        evaluation_summary = client.get("/api/evaluations/summary")
        evaluation_summary_passed = (
            evaluation_summary.status_code == 200
            and evaluation_summary.json()["run_count"] == 2
            and evaluation_summary.json()["average_routing_score"] == 1.0
        )
        print("PASS evaluation_summary" if evaluation_summary_passed else "FAIL evaluation_summary")
        if not evaluation_summary_passed:
            failures.append("evaluation_summary did not return an empty safe baseline")
        audit_export = client.get("/api/audit-events/export")
        audit_export.raise_for_status()
        audit_events = audit_export.json()["events"]
        chain_is_intact = all(
            event["previous_event_hash"] == audit_events[index - 1]["event_hash"]
            for index, event in enumerate(audit_events)
            if index > 0
        )
        audit_export_passed = (
            bool(audit_events)
            and chain_is_intact
            and audit_export.json()["chain_head"] == audit_events[-1]["event_hash"]
            and any(event["action"] == "review.decision_created" for event in audit_events)
        )
        print("PASS audit_export_chain" if audit_export_passed else "FAIL audit_export_chain")
        if not audit_export_passed:
            failures.append("audit_export_chain did not preserve the event chain")

        from app.config import Settings

        production_rejected = False
        try:
            Settings(environment="production").validate_production_configuration()
        except ValueError:
            production_rejected = True
        print("PASS production_configuration_guard" if production_rejected else "FAIL production_configuration_guard")
        if not production_rejected:
            failures.append("production_configuration_guard accepted unsafe defaults")

        if failures:
            raise SystemExit("Evaluation failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
