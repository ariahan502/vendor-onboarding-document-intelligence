"use client";

import { useEffect, useMemo, useState } from "react";

import type { DocumentSummary, EvidenceSummary } from "../types/packages";
import { getDocumentUrl } from "../lib/api";
import { EmptyState } from "./empty-state";

type DocumentViewerProps = {
  document: DocumentSummary | null;
  evidence: EvidenceSummary[];
  selectedFindingId: string | null;
};

export function DocumentViewer({
  document,
  evidence,
  selectedFindingId,
}: DocumentViewerProps) {
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(
    evidence[0]?.evidence_id ?? null,
  );
  const [currentPage, setCurrentPage] = useState<number>(evidence[0]?.page_num ?? 1);

  useEffect(() => {
    setSelectedEvidenceId(evidence[0]?.evidence_id ?? null);
    setCurrentPage(evidence[0]?.page_num ?? 1);
  }, [document?.document_id, evidence]);

  const selectedEvidence =
    evidence.find((item) => item.evidence_id === selectedEvidenceId) ?? evidence[0] ?? null;

  const pageCount = document?.page_count ?? 1;
  const pageNumbers = useMemo(
    () => Array.from({ length: Math.max(pageCount, 1) }, (_value, index) => index + 1),
    [pageCount],
  );

  if (!document) {
    return (
      <EmptyState
        eyebrow="Viewer"
        title="No document selected"
        body="This packet is not ready for document review yet. When files are available, the source viewer will appear here."
      />
    );
  }

  return (
    <div
      style={{
        marginTop: 16,
        border: "1px dashed var(--line)",
        borderRadius: 22,
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.7), rgba(244,239,230,0.7))",
        minHeight: 760,
        padding: 24,
        display: "grid",
        alignContent: "start",
        gap: 18,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", color: "var(--muted)" }}>
        <span>Viewer focus: {document.doc_type.replaceAll("_", " ")}</span>
        <span>
          Page {currentPage} of {pageCount}
        </span>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {pageNumbers.map((page) => (
          <button
            key={page}
            type="button"
            onClick={() => setCurrentPage(page)}
            style={{
              border: "1px solid var(--line)",
              borderRadius: 999,
              padding: "7px 12px",
              background:
                page === currentPage ? "var(--accent-soft)" : "rgba(255, 255, 255, 0.72)",
              color: page === currentPage ? "var(--accent)" : "var(--muted)",
              cursor: "pointer",
            }}
          >
            Page {page}
          </button>
        ))}
      </div>

      {selectedFindingId ? (
        <div
          style={{
            fontSize: 13,
            color: "var(--accent)",
            padding: "8px 10px",
            borderRadius: 12,
            background: "rgba(191, 91, 44, 0.08)",
            width: "fit-content",
          }}
        >
          Filtered by selected finding
        </div>
      ) : null}

      <div
        style={{
          border: "1px solid var(--line)",
          borderRadius: 20,
          background: "rgba(255,255,255,0.78)",
          minHeight: 340,
          padding: 24,
          display: "grid",
          gap: 14,
        }}
        >
          <div
            style={{
            display: "flex",
            justifyContent: "space-between",
            gap: 12,
            alignItems: "center",
          }}
          >
            <strong style={{ fontSize: 18 }}>{document.file_name}</strong>
            <span style={{ fontSize: 13, color: "var(--muted)" }}>
              OCR {document.ocr_status} • Parse {document.parse_status}
            </span>
          </div>

          {document.ocr_status === "required" ? (
            <div
              style={{
                border: "1px solid rgba(139, 90, 20, 0.28)",
                borderRadius: 14,
                padding: 14,
                background: "rgba(139, 90, 20, 0.08)",
                color: "var(--warn)",
                lineHeight: 1.5,
              }}
            >
              This PDF has no extractable text layer. OCR must be configured before fields can
              be extracted automatically; review the original document manually in the meantime.
            </div>
          ) : null}

          {document.mime_type === "application/pdf" && document.file_path ? (
            <div
              style={{
                border: "1px solid rgba(72, 53, 41, 0.12)",
                borderRadius: 18,
                overflow: "hidden",
                background: "white",
              }}
            >
              <object
                data={`${getDocumentUrl(document.file_path)}#page=${currentPage}`}
                type="application/pdf"
                style={{ width: "100%", minHeight: 420 }}
              >
                <div
                  style={{
                    padding: 20,
                    color: "var(--muted)",
                    lineHeight: 1.7,
                  }}
                >
                  This browser could not embed the PDF directly. Open the source file
                  in a new tab to inspect it.
                </div>
              </object>
            </div>
          ) : null}

          <div
            style={{
              border: "1px solid rgba(72, 53, 41, 0.12)",
              borderRadius: 18,
              padding: 20,
              minHeight: 220,
              background:
                "linear-gradient(180deg, rgba(255,255,255,1), rgba(250,246,239,0.94))",
            }}
          >
            <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 14 }}>
              Page {currentPage} focus summary
            </div>

            {selectedEvidence && selectedEvidence.page_num === currentPage ? (
              <div
                style={{
                  borderLeft: "4px solid var(--accent)",
                  paddingLeft: 14,
                  display: "grid",
                  gap: 8,
                }}
              >
                <span style={{ fontSize: 12, color: "var(--accent)", textTransform: "uppercase" }}>
                  Focused evidence
                </span>
                <div style={{ fontSize: 19, lineHeight: 1.6 }}>{selectedEvidence.snippet_text}</div>
              </div>
            ) : (
              <div style={{ color: "var(--muted)", fontSize: 16, lineHeight: 1.7 }}>
                No focused evidence on this page yet. Select an evidence card below or choose
                a different finding to inspect highlighted source context.
              </div>
            )}
          </div>
      </div>

      {evidence.length > 0 ? (
        <div style={{ display: "grid", gap: 10 }}>
          <strong style={{ fontSize: 15 }}>Evidence Timeline</strong>
          {evidence.map((item) => {
            const isActive = item.evidence_id === selectedEvidence?.evidence_id;
            return (
              <button
                key={item.evidence_id}
                type="button"
                onClick={() => {
                  setSelectedEvidenceId(item.evidence_id);
                  setCurrentPage(item.page_num ?? 1);
                }}
                style={{
                  border: "1px solid var(--line)",
                  borderRadius: 18,
                  padding: 16,
                  background: isActive
                    ? "rgba(191, 91, 44, 0.14)"
                    : "rgba(255,255,255,0.66)",
                  boxShadow: "inset 0 0 0 1px rgba(191, 91, 44, 0.06)",
                  textAlign: "left",
                  cursor: "pointer",
                  display: "grid",
                  gap: 8,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    color: "var(--accent)",
                    fontSize: 13,
                  }}
                >
                  <span>{item.document_name}</span>
                  <span>Page {item.page_num ?? "?"}</span>
                </div>
                <div style={{ fontSize: 18, lineHeight: 1.55 }}>{item.snippet_text}</div>
              </button>
            );
          })}
        </div>
      ) : (
        <EmptyState
          eyebrow="Evidence"
          title="No evidence snippets match this selection"
          body="Choose a different finding or document to inspect another piece of source evidence."
        />
      )}
    </div>
  );
}
