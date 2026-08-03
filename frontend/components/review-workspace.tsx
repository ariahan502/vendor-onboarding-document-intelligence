"use client";

import { useMemo, useState } from "react";

import type { PackageDetailResponse } from "../types/packages";
import { formatDateTime } from "../lib/format";
import { DecisionPanel } from "./decision-panel";
import { DocumentViewer } from "./document-viewer";
import { EmptyState } from "./empty-state";
import { FieldOverrideForm } from "./field-override-form";
import { FindingResolutionForm } from "./finding-resolution-form";
import { ProcessingSimulator } from "./processing-simulator";

type ReviewWorkspaceProps = {
  packet: PackageDetailResponse;
};

export function ReviewWorkspace({ packet }: ReviewWorkspaceProps) {
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(
    packet.documents[0]?.document_id ?? null,
  );
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(
    packet.findings[0]?.finding_id ?? null,
  );

  const selectedDocument =
    packet.documents.find((document) => document.document_id === selectedDocumentId) ??
    packet.documents[0] ??
    null;
  const selectedFinding =
    packet.findings.find((finding) => finding.finding_id === selectedFindingId) ?? null;
  const latestFindingResolution = selectedFinding
    ? packet.finding_resolutions.find(
        (resolution) => resolution.finding_id === selectedFinding.finding_id,
      ) ?? null
    : null;
  const latestReview = packet.review_history[0] ?? null;
  const missingRequiredCount = packet.requirements.filter(
    (requirement) => requirement.is_required && !requirement.is_satisfied,
  ).length;
  const processingSummary = summarizeProcessing(packet.processing_runs);

  const visibleEvidence = useMemo(() => {
    if (selectedFindingId) {
      const matched = packet.evidence.filter(
        (item) => item.related_finding_id === selectedFindingId,
      );
      if (matched.length > 0) {
        return matched;
      }
    }

    if (selectedDocument) {
      const matched = packet.evidence.filter(
        (item) => item.document_id === selectedDocument.document_id,
      );
      if (matched.length > 0) {
        return matched;
      }
    }

    return packet.evidence;
  }, [packet.evidence, selectedDocument, selectedFindingId]);

  const severityCounts = packet.findings.reduce<Record<string, number>>((counts, finding) => {
    counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
    return counts;
  }, {});

  const visibleFields = packet.extracted_fields.filter((field) =>
    selectedDocument ? field.source_document_id === selectedDocument.document_id : true,
  );
  const latestOverrideByField = packet.field_overrides.reduce<Record<string, (typeof packet.field_overrides)[number]>>(
    (overrides, override) => {
      if (!overrides[override.field_id]) overrides[override.field_id] = override;
      return overrides;
    },
    {},
  );

  return (
    <main className="page-shell">
      <div className="page-frame" style={{ display: "grid", gap: 20 }}>
        <header
          className="hero-card"
          style={{
            padding: 24,
            display: "grid",
            gap: 14,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
            <div style={{ display: "grid", gap: 6 }}>
              <a href="/" style={{ color: "var(--muted)", fontSize: 14 }}>
                ← Back to queue
              </a>
              <h1 style={{ margin: 0, fontSize: 36 }}>{packet.vendor_name}</h1>
              <p style={{ margin: 0, color: "var(--muted)" }}>
                {packet.package_id} • Submitted {formatDateTime(packet.submitted_at)}
              </p>
            </div>
            <div style={{ display: "grid", gap: 8, justifyItems: "end" }}>
              <StatusBadge label={packet.package_status} tone="neutral" />
              <StatusBadge
                label={packet.system_recommendation ?? "pending"}
                tone={recommendationTone(packet.system_recommendation)}
              />
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 12,
            }}
          >
            <InfoTile label="Assigned Reviewer" value={packet.assigned_reviewer ?? "Unassigned"} />
            <InfoTile label="Priority Score" value={String(packet.priority_score ?? "—")} />
            <InfoTile label="Final Decision" value={packet.final_decision ?? "Pending"} />
            <InfoTile label="Open Findings" value={String(packet.findings.length)} />
            <InfoTile label="Missing Required Docs" value={String(missingRequiredCount)} />
            <InfoTile label="Pipeline State" value={processingSummary.label} />
          </div>
        </header>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "280px minmax(0, 1fr) 380px",
            gap: 20,
            alignItems: "start",
          }}
        >
          <aside className="surface-card" style={{ padding: 18, display: "grid", gap: 18 }}>
            <PanelTitle eyebrow="Packet" title="Document List" />
            {packet.documents.length === 0 ? (
              <EmptyState
                eyebrow="Documents"
                title="Documents are still being processed"
                body="This packet does not yet have parsed documents ready for review. Once OCR and extraction complete, the document list will appear here."
                actionLabel="Back to queue"
                actionHref="/"
              />
            ) : (
              <div style={{ display: "grid", gap: 10 }}>
                {packet.documents.map((document) => {
                  const isActive = document.document_id === selectedDocument?.document_id;
                  return (
                    <button
                      key={document.document_id}
                      type="button"
                      onClick={() => setSelectedDocumentId(document.document_id)}
                      style={{
                        border: "1px solid var(--line)",
                        borderRadius: 18,
                        padding: 14,
                        background: isActive ? "var(--accent-soft)" : "var(--panel-strong)",
                        display: "grid",
                        gap: 6,
                        textAlign: "left",
                        cursor: "pointer",
                      }}
                    >
                      <strong>{document.file_name}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 13 }}>
                        {document.doc_type} • {document.page_count ?? "?"} pages
                      </span>
                      <span style={{ color: "var(--muted)", fontSize: 13 }}>
                        OCR {document.ocr_status} • Parse {document.parse_status}
                      </span>
                      {document.ocr_status === "required" ? (
                        <span style={{ color: "var(--warn)", fontSize: 13 }}>
                          OCR provider needed for this scanned PDF
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            )}

            <div style={{ display: "grid", gap: 10 }}>
              <PanelTitle eyebrow="Checklist" title="Requirements" />
              {packet.requirements.map((requirement) => (
                <div
                  key={requirement.required_doc_type}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    borderBottom: "1px solid var(--line)",
                    paddingBottom: 10,
                  }}
                >
                  <span style={{ textTransform: "capitalize" }}>
                    {requirement.required_doc_type.replaceAll("_", " ")}
                  </span>
                  <span
                    style={{
                      color: requirement.is_satisfied ? "var(--ok)" : "var(--danger)",
                      fontSize: 13,
                    }}
                  >
                    {requirement.is_satisfied ? "satisfied" : "missing"}
                  </span>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <PanelTitle eyebrow="Pipeline" title="Processing Timeline" />
              {packet.processing_runs.length > 0 ? (
                packet.processing_runs.map((run) => (
                  <div
                    key={run.processing_run_id}
                    style={{
                      border: "1px solid var(--line)",
                      borderRadius: 16,
                      padding: 14,
                      background: "var(--panel-strong)",
                      display: "grid",
                      gap: 6,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: 10,
                        alignItems: "center",
                        flexWrap: "wrap",
                      }}
                    >
                      <strong>{humanizeRunType(run.run_type)}</strong>
                      <StatusBadge label={run.run_status} tone={runStatusTone(run.run_status)} />
                    </div>
                    <span style={{ color: "var(--muted)", fontSize: 13 }}>
                      {run.document_name ?? "Package-level step"}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 13 }}>
                      Started {formatDateTime(run.started_at)}
                      {run.completed_at ? ` • Finished ${formatDateTime(run.completed_at)}` : ""}
                    </span>
                    {run.model_name ? (
                      <span style={{ fontSize: 13 }}>
                        Model {run.model_name}
                        {run.prompt_version ? ` • prompt ${run.prompt_version}` : ""}
                      </span>
                    ) : null}
                    {run.error_message ? (
                      <span style={{ color: "var(--danger)", fontSize: 13 }}>
                        {run.error_message}
                      </span>
                    ) : null}
                  </div>
                ))
              ) : (
                <EmptyState
                  eyebrow="Pipeline"
                  title="No processing telemetry yet"
                  body="This packet does not yet have ingestion, OCR, extraction, or validation run records."
                />
              )}
            </div>
          </aside>

          <section className="surface-card" style={{ padding: 18, minHeight: 900 }}>
            <PanelTitle
              eyebrow="Source Document"
              title={selectedDocument?.file_name ?? "Document viewer"}
            />
            <DocumentViewer
              document={selectedDocument}
              evidence={visibleEvidence}
              selectedFindingId={selectedFindingId}
            />
          </section>

          <aside className="surface-card" style={{ padding: 18, display: "grid", gap: 18 }}>
            <PanelTitle eyebrow="Review" title="Fields, Findings, and Decision" />

            <div
              style={{
                border: "1px solid var(--line)",
                borderRadius: 18,
                padding: 16,
                background: "var(--panel-strong)",
                display: "grid",
                gap: 12,
              }}
            >
              <SectionLabel label="Review Focus" />
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
                  gap: 10,
                }}
              >
                <MiniStat
                  label="High"
                  value={String((severityCounts.high ?? 0) + (severityCounts.critical ?? 0))}
                  tone="danger"
                />
                <MiniStat label="Medium" value={String(severityCounts.medium ?? 0)} tone="warn" />
                <MiniStat label="Low" value={String(severityCounts.low ?? 0)} tone="ok" />
                <MiniStat label="Evidence" value={String(visibleEvidence.length)} tone="neutral" />
              </div>
              <div style={{ display: "grid", gap: 6 }}>
                <span style={{ color: "var(--muted)", fontSize: 13 }}>Current blocker</span>
                <strong style={{ fontSize: 15 }}>
                  {selectedFinding?.title ??
                    packet.notes ??
                    "No active finding is selected. Review document evidence and choose a decision."}
                </strong>
              {selectedFinding?.description ? (
                <span style={{ color: "var(--muted)", fontSize: 14 }}>
                  {selectedFinding.description}
                </span>
              ) : null}
              {selectedFinding ? (
                <span style={{ color: "var(--muted)", fontSize: 13 }}>
                  Finding status: {selectedFinding.finding_status.replaceAll("_", " ")}
                </span>
              ) : null}
              {latestFindingResolution ? (
                <span style={{ color: "var(--accent)", fontSize: 13 }}>
                  {latestFindingResolution.resolution_status.replaceAll("_", " ")} by {latestFindingResolution.reviewer}: {latestFindingResolution.resolution_note}
                </span>
              ) : null}
              {selectedFinding?.finding_status === "open" ? (
                <FindingResolutionForm
                  packageId={packet.package_id}
                  findingId={selectedFinding.finding_id}
                />
              ) : null}
              </div>
              {latestReview?.reviewer_comment ? (
                <div
                  style={{
                    borderTop: "1px solid var(--line)",
                    paddingTop: 10,
                    display: "grid",
                    gap: 4,
                  }}
                >
                  <span style={{ color: "var(--muted)", fontSize: 13 }}>
                    Latest review note • {formatDateTime(latestReview.decision_at)}
                  </span>
                  <span style={{ fontSize: 14 }}>{latestReview.reviewer_comment}</span>
                </div>
              ) : null}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <SectionLabel label="Extracted Fields" />
              {visibleFields.length > 0 ? (
                visibleFields.map((field) => {
                  const override = latestOverrideByField[field.field_id];
                  return (
                    <div
                    key={`${field.field_name}-${field.source_document_id}-${field.source_page}`}
                    style={{
                      border: "1px solid var(--line)",
                      borderRadius: 16,
                      padding: 14,
                      display: "grid",
                      gap: 6,
                      background: "var(--panel-strong)",
                    }}
                  >
                    <strong style={{ textTransform: "capitalize" }}>
                      {field.field_name.replaceAll("_", " ")}
                    </strong>
                    <span>{override?.corrected_value ?? field.raw_value ?? "—"}</span>
                    {override ? (
                      <span style={{ color: "var(--accent)", fontSize: 13 }}>
                        Corrected by {override.reviewer}: {override.correction_reason}
                      </span>
                    ) : null}
                    {field.normalized_value ? (
                      <span style={{ color: "var(--muted)", fontSize: 13 }}>
                        normalized: {field.normalized_value}
                      </span>
                    ) : null}
                    <span style={{ color: "var(--muted)", fontSize: 13 }}>
                      confidence {field.confidence ?? "—"} • page {field.source_page ?? "?"}
                    </span>
                    {field.field_id ? (
                      <FieldOverrideForm
                        packageId={packet.package_id}
                        fieldId={field.field_id}
                        originalValue={field.raw_value}
                      />
                    ) : null}
                  </div>
                  );
                })
              ) : (
                <EmptyState
                  eyebrow="Fields"
                  title="No extracted fields for this document"
                  body="This selected document does not yet have structured fields ready, or the extraction result belongs to a different document in the packet."
                />
              )}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <SectionLabel label="Findings" />
              {packet.findings.length > 0 ? (
                packet.findings.map((finding) => {
                  const isActive = finding.finding_id === selectedFindingId;
                  return (
                    <button
                      key={finding.finding_id}
                      type="button"
                      onClick={() =>
                        setSelectedFindingId((current) =>
                          current === finding.finding_id ? null : finding.finding_id,
                        )
                      }
                      style={{
                        border: "1px solid var(--line)",
                        borderRadius: 16,
                        padding: 14,
                        background: isActive
                          ? "rgba(191, 91, 44, 0.14)"
                          : severityBackground(finding.severity),
                        display: "grid",
                        gap: 6,
                        textAlign: "left",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                        <strong>{finding.title}</strong>
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                          <StatusBadge label={finding.finding_status} tone={finding.finding_status === "open" ? "neutral" : "ok"} />
                          <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} />
                        </div>
                      </div>
                      <span style={{ color: "var(--muted)", fontSize: 14 }}>
                        {finding.description}
                      </span>
                      {finding.suggested_action ? (
                        <span style={{ fontSize: 14 }}>
                          Next step: {finding.suggested_action}
                        </span>
                      ) : null}
                    </button>
                  );
                })
              ) : (
                <EmptyState
                  eyebrow="Findings"
                  title="No findings are currently open"
                  body="This packet does not yet have mismatch, policy, or confidence findings to review."
                />
              )}
            </div>

            <div style={{ display: "grid", gap: 12 }}>
              <ProcessingSimulator
                packageId={packet.package_id}
                packageStatus={packet.package_status}
                processingStateLabel={processingSummary.label}
              />
              <SectionLabel label="Decision Panel" />
              <DecisionPanel
                packageId={packet.package_id}
                systemRecommendation={packet.system_recommendation}
                notes={packet.notes}
                openHighRiskFindings={packet.findings
                  .filter(
                    (finding) =>
                      finding.finding_status === "open" &&
                      (finding.severity === "high" || finding.severity === "critical"),
                  )
                  .map((finding) => finding.title)}
              />
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <SectionLabel label="Review History" />
              {packet.review_history.length > 0 ? (
                packet.review_history.map((decision) => (
                  <div
                    key={decision.decision_id}
                    style={{
                      borderTop: "1px solid var(--line)",
                      paddingTop: 10,
                      display: "grid",
                      gap: 4,
                    }}
                  >
                    <strong>{decision.final_decision.replaceAll("_", " ")}</strong>
                    <span style={{ color: "var(--muted)", fontSize: 13 }}>
                      {decision.reviewer} • {formatDateTime(decision.decision_at)}
                    </span>
                    {decision.reviewer_comment ? (
                      <span style={{ fontSize: 14 }}>{decision.reviewer_comment}</span>
                    ) : null}
                  </div>
                ))
              ) : (
                <EmptyState
                  eyebrow="History"
                  title="No review history yet"
                  body="This packet has not yet been reviewed or overridden by a human reviewer."
                />
              )}
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}

function PanelTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <span
        style={{
          color: "var(--accent)",
          fontSize: 12,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
        }}
      >
        {eyebrow}
      </span>
      <h2 style={{ margin: 0, fontSize: 24 }}>{title}</h2>
    </div>
  );
}

function SectionLabel({ label }: { label: string }) {
  return <strong style={{ fontSize: 15 }}>{label}</strong>;
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        border: "1px solid var(--line)",
        borderRadius: 16,
        padding: 14,
        background: "var(--panel-strong)",
      }}
    >
      <div style={{ color: "var(--muted)", fontSize: 13 }}>{label}</div>
      <div style={{ marginTop: 6, fontSize: 18 }}>{value}</div>
    </div>
  );
}

function MiniStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "neutral" | "danger" | "warn" | "ok";
}) {
  const map = {
    neutral: ["rgba(51, 44, 39, 0.08)", "var(--text)"],
    danger: ["rgba(170, 59, 47, 0.14)", "var(--danger)"],
    warn: ["rgba(139, 90, 20, 0.14)", "var(--warn)"],
    ok: ["rgba(47, 108, 85, 0.14)", "var(--ok)"],
  } as const;
  const [background, color] = map[tone];

  return (
    <div
      style={{
        borderRadius: 14,
        padding: 12,
        background,
        display: "grid",
        gap: 4,
      }}
    >
      <span style={{ color: "var(--muted)", fontSize: 12 }}>{label}</span>
      <strong style={{ color, fontSize: 18 }}>{value}</strong>
    </div>
  );
}

function StatusBadge({
  label,
  tone,
}: {
  label: string;
  tone: "neutral" | "danger" | "warn" | "ok";
}) {
  const map = {
    neutral: ["rgba(51, 44, 39, 0.08)", "var(--text)"],
    danger: ["rgba(170, 59, 47, 0.14)", "var(--danger)"],
    warn: ["rgba(139, 90, 20, 0.14)", "var(--warn)"],
    ok: ["rgba(47, 108, 85, 0.14)", "var(--ok)"],
  } as const;

  const [background, color] = map[tone];

  return (
    <span
      style={{
        display: "inline-flex",
        width: "fit-content",
        borderRadius: 999,
        padding: "6px 10px",
        background,
        color,
        fontSize: 13,
        textTransform: "capitalize",
      }}
    >
      {label.replaceAll("_", " ")}
    </span>
  );
}

function recommendationTone(status: string | null) {
  if (status === "approve") return "ok";
  if (status === "escalate") return "danger";
  if (status === "needs_review") return "warn";
  return "neutral";
}

function severityTone(status: string) {
  if (status === "high" || status === "critical") return "danger";
  if (status === "medium") return "warn";
  if (status === "low") return "ok";
  return "neutral";
}

function severityBackground(status: string) {
  if (status === "high" || status === "critical") {
    return "rgba(170, 59, 47, 0.08)";
  }
  if (status === "medium") {
    return "rgba(191, 91, 44, 0.08)";
  }
  return "rgba(47, 108, 85, 0.08)";
}

function runStatusTone(status: string) {
  if (status === "failed") return "danger";
  if (status === "running" || status === "queued") return "warn";
  if (status === "completed") return "ok";
  return "neutral";
}

function humanizeRunType(runType: string) {
  return runType.replaceAll("_", " ");
}

function summarizeProcessing(
  processingRuns: PackageDetailResponse["processing_runs"],
): { label: string } {
  if (processingRuns.some((run) => run.run_status === "failed")) {
    return { label: "Failed" };
  }
  if (processingRuns.some((run) => run.run_status === "running")) {
    return { label: "In Progress" };
  }
  if (processingRuns.length > 0 && processingRuns.every((run) => run.run_status === "completed")) {
    return { label: "Completed" };
  }
  if (processingRuns.length > 0) {
    return { label: "Queued" };
  }
  return { label: "Not Started" };
}
