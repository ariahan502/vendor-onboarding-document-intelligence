"""Initial vendor onboarding schema.

Revision ID: 20260730_0001
Revises:
Create Date: 2026-07-30 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# SQLite powers local development while PostgreSQL keeps its native JSONB storage.
JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


revision = "20260730_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("vendor_id", sa.Text(), primary_key=True),
        sa.Column("legal_name", sa.Text(), nullable=False),
        sa.Column("normalized_legal_name", sa.Text(), nullable=True),
        sa.Column("tax_id", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "document_packages",
        sa.Column("package_id", sa.Text(), primary_key=True),
        sa.Column(
            "vendor_id",
            sa.Text(),
            sa.ForeignKey("vendors.vendor_id"),
            nullable=False,
        ),
        sa.Column("package_status", sa.Text(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("assigned_reviewer", sa.Text(), nullable=True),
        sa.Column("system_recommendation", sa.Text(), nullable=True),
        sa.Column("final_decision", sa.Text(), nullable=True),
        sa.Column("priority_score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_document_packages_vendor_id",
        "document_packages",
        ["vendor_id"],
        unique=False,
    )

    op.create_table(
        "document_requirements",
        sa.Column("requirement_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column("required_doc_type", sa.Text(), nullable=False),
        sa.Column(
            "is_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "is_satisfied",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("missing_reason", sa.Text(), nullable=True),
    )

    op.create_table(
        "documents",
        sa.Column("document_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column("doc_type", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("document_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("upload_status", sa.Text(), nullable=False, server_default="uploaded"),
        sa.Column("ocr_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("parse_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_documents_package_id", "documents", ["package_id"], unique=False)

    op.create_table(
        "processing_runs",
        sa.Column("processing_run_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Text(),
            sa.ForeignKey("documents.document_id"),
            nullable=True,
        ),
        sa.Column("run_type", sa.Text(), nullable=False),
        sa.Column("run_status", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    op.create_table(
        "extracted_fields",
        sa.Column("field_id", sa.Text(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Text(),
            sa.ForeignKey("documents.document_id"),
            nullable=False,
        ),
        sa.Column(
            "processing_run_id",
            sa.Text(),
            sa.ForeignKey("processing_runs.processing_run_id"),
            nullable=True,
        ),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("value_type", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_span_text", sa.Text(), nullable=True),
        sa.Column("source_bbox", JSON_TYPE, nullable=True),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_extracted_fields_document_id",
        "extracted_fields",
        ["document_id"],
        unique=False,
    )

    op.create_table(
        "field_normalizations",
        sa.Column("normalization_id", sa.Text(), primary_key=True),
        sa.Column(
            "field_id",
            sa.Text(),
            sa.ForeignKey("extracted_fields.field_id"),
            nullable=False,
        ),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column(
            "normalized_value_json",
            JSON_TYPE,
            nullable=True,
        ),
        sa.Column("normalization_method", sa.Text(), nullable=False),
        sa.Column("normalization_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "field_comparisons",
        sa.Column("comparison_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column(
            "left_field_id",
            sa.Text(),
            sa.ForeignKey("extracted_fields.field_id"),
            nullable=False,
        ),
        sa.Column(
            "right_field_id",
            sa.Text(),
            sa.ForeignKey("extracted_fields.field_id"),
            nullable=False,
        ),
        sa.Column("comparison_type", sa.Text(), nullable=False),
        sa.Column("comparison_status", sa.Text(), nullable=False),
        sa.Column("similarity_score", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "requires_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_field_comparisons_package_id",
        "field_comparisons",
        ["package_id"],
        unique=False,
    )

    op.create_table(
        "policy_rules",
        sa.Column("rule_id", sa.Text(), primary_key=True),
        sa.Column("rule_name", sa.Text(), nullable=False),
        sa.Column("rule_code", sa.Text(), nullable=False, unique=True),
        sa.Column("rule_description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("decision_impact", sa.Text(), nullable=True),
        sa.Column("condition_expression", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "routing_policies",
        sa.Column("routing_policy_id", sa.Text(), primary_key=True),
        sa.Column("policy_name", sa.Text(), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("routing_expression", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "validation_findings",
        sa.Column("finding_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.Text(),
            sa.ForeignKey("documents.document_id"),
            nullable=True,
        ),
        sa.Column(
            "comparison_id",
            sa.Text(),
            sa.ForeignKey("field_comparisons.comparison_id"),
            nullable=True,
        ),
        sa.Column(
            "rule_id",
            sa.Text(),
            sa.ForeignKey("policy_rules.rule_id"),
            nullable=True,
        ),
        sa.Column("finding_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("finding_status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("suggested_action", sa.Text(), nullable=True),
        sa.Column(
            "requires_human_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_validation_findings_package_id",
        "validation_findings",
        ["package_id"],
        unique=False,
    )

    op.create_table(
        "decision_evidence",
        sa.Column("evidence_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column(
            "finding_id",
            sa.Text(),
            sa.ForeignKey("validation_findings.finding_id"),
            nullable=True,
        ),
        sa.Column(
            "field_id",
            sa.Text(),
            sa.ForeignKey("extracted_fields.field_id"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            sa.Text(),
            sa.ForeignKey("documents.document_id"),
            nullable=True,
        ),
        sa.Column("evidence_type", sa.Text(), nullable=False),
        sa.Column("page_num", sa.Integer(), nullable=True),
        sa.Column("snippet_text", sa.Text(), nullable=True),
        sa.Column("bbox", JSON_TYPE, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_decision_evidence_package_id",
        "decision_evidence",
        ["package_id"],
        unique=False,
    )

    op.create_table(
        "review_decisions",
        sa.Column("decision_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=False,
        ),
        sa.Column("reviewer", sa.Text(), nullable=False),
        sa.Column("system_recommendation", sa.Text(), nullable=True),
        sa.Column("final_decision", sa.Text(), nullable=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("reviewer_comment", sa.Text(), nullable=True),
        sa.Column(
            "decision_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_review_decisions_package_id",
        "review_decisions",
        ["package_id"],
        unique=False,
    )

    op.create_table(
        "evaluation_cases",
        sa.Column("eval_case_id", sa.Text(), primary_key=True),
        sa.Column(
            "package_id",
            sa.Text(),
            sa.ForeignKey("document_packages.package_id"),
            nullable=True,
        ),
        sa.Column("case_name", sa.Text(), nullable=False),
        sa.Column("case_slice", sa.Text(), nullable=True),
        sa.Column(
            "expected_fields",
            JSON_TYPE,
            nullable=True,
        ),
        sa.Column(
            "expected_findings",
            JSON_TYPE,
            nullable=True,
        ),
        sa.Column("expected_decision", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "evaluation_runs",
        sa.Column("eval_run_id", sa.Text(), primary_key=True),
        sa.Column(
            "eval_case_id",
            sa.Text(),
            sa.ForeignKey("evaluation_cases.eval_case_id"),
            nullable=False,
        ),
        sa.Column("run_label", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("model_version", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=True),
        sa.Column("rule_version", sa.Text(), nullable=True),
        sa.Column("extraction_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("finding_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("routing_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("reviewer_agreement_score", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "run_started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("run_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_evaluation_runs_case_id",
        "evaluation_runs",
        ["eval_case_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_evaluation_runs_case_id", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_cases")
    op.drop_index("idx_review_decisions_package_id", table_name="review_decisions")
    op.drop_table("review_decisions")
    op.drop_index("idx_decision_evidence_package_id", table_name="decision_evidence")
    op.drop_table("decision_evidence")
    op.drop_index("idx_validation_findings_package_id", table_name="validation_findings")
    op.drop_table("validation_findings")
    op.drop_table("routing_policies")
    op.drop_table("policy_rules")
    op.drop_index("idx_field_comparisons_package_id", table_name="field_comparisons")
    op.drop_table("field_comparisons")
    op.drop_table("field_normalizations")
    op.drop_index("idx_extracted_fields_document_id", table_name="extracted_fields")
    op.drop_table("extracted_fields")
    op.drop_table("processing_runs")
    op.drop_index("idx_documents_package_id", table_name="documents")
    op.drop_table("documents")
    op.drop_table("document_requirements")
    op.drop_index("idx_document_packages_vendor_id", table_name="document_packages")
    op.drop_table("document_packages")
    op.drop_table("vendors")
