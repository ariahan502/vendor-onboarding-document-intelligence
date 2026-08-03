"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { postCreatePackage, postUploadDocument } from "../lib/api";

const AVAILABLE_DOCUMENTS = [
  {
    doc_type: "contract",
    label: "Signed Contract",
  },
  {
    doc_type: "w9",
    label: "W-9",
  },
  {
    doc_type: "insurance_certificate",
    label: "Insurance Certificate",
  },
] as const;

export function SubmissionForm() {
  const router = useRouter();
  const [vendorName, setVendorName] = useState("");
  const [taxId, setTaxId] = useState("");
  const [category, setCategory] = useState("consulting");
  const [reviewer, setReviewer] = useState("aria.han");
  const [documentFiles, setDocumentFiles] = useState<Record<string, File | null>>({
    contract: null,
    w9: null,
    insurance_certificate: null,
  });
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    try {
      setSubmitting(true);
      setStatusMessage(null);

      const submittedDocuments = AVAILABLE_DOCUMENTS.filter(
        (document) => documentFiles[document.doc_type],
      ).map((document) => ({
        doc_type: document.doc_type,
        file_name: documentFiles[document.doc_type]?.name ?? "uploaded-document.pdf",
      }));

      const result = await postCreatePackage({
        vendor_name: vendorName,
        tax_id: taxId || null,
        country: "US",
        category: category || null,
        assigned_reviewer: reviewer || null,
        submitted_documents: submittedDocuments,
      });

      await Promise.all(
        AVAILABLE_DOCUMENTS.flatMap((document) => {
          const file = documentFiles[document.doc_type];
          return file ? [postUploadDocument(result.package_id, document.doc_type, file)] : [];
        }),
      );

      router.push(`/packages/${result.package_id}`);
      router.refresh();
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Failed to create onboarding package.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="surface-card"
      style={{ padding: 24, display: "grid", gap: 18, maxWidth: 820 }}
    >
      <div style={{ display: "grid", gap: 6 }}>
        <span
          style={{
            color: "var(--accent)",
            fontSize: 12,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
          }}
        >
          Intake
        </span>
        <h1 style={{ margin: 0, fontSize: 38 }}>Create Vendor Packet</h1>
        <p style={{ margin: 0, color: "var(--muted)", fontSize: 16 }}>
          Capture vendor basics, attach the available PDFs, and send the packet into
          processing. Files stay on this local development machine.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 14,
        }}
      >
        <label style={{ display: "grid", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>Vendor legal name</span>
          <input
            value={vendorName}
            onChange={(event) => setVendorName(event.target.value)}
            placeholder="ABC Consulting LLC"
            style={inputStyle}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>Tax ID</span>
          <input
            value={taxId}
            onChange={(event) => setTaxId(event.target.value)}
            placeholder="12-3456789"
            style={inputStyle}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>Category</span>
          <input
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            placeholder="consulting"
            style={inputStyle}
          />
        </label>

        <label style={{ display: "grid", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--muted)" }}>Assigned reviewer</span>
          <input
            value={reviewer}
            onChange={(event) => setReviewer(event.target.value)}
            placeholder="aria.han"
            style={inputStyle}
          />
        </label>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        <strong style={{ fontSize: 16 }}>Submitted PDFs</strong>
        <div style={{ display: "grid", gap: 10 }}>
          {AVAILABLE_DOCUMENTS.map((document) => (
            <label
              key={document.doc_type}
              style={{
                display: "flex",
                gap: 10,
                alignItems: "center",
                border: "1px solid var(--line)",
                borderRadius: 14,
                padding: 14,
                background: "var(--panel-strong)",
              }}
            >
              <div style={{ display: "grid", gap: 2 }}>
                <strong>{document.label}</strong>
                <span style={{ color: "var(--muted)", fontSize: 13 }}>
                  PDF only, up to 10 MB. Leave empty when the vendor has not submitted it.
                </span>
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={(event) =>
                    setDocumentFiles((current) => ({
                      ...current,
                      [document.doc_type]: event.target.files?.[0] ?? null,
                    }))
                  }
                  style={{ marginTop: 8, maxWidth: "100%" }}
                />
              </div>
            </label>
          ))}
        </div>
      </div>

      <div
        style={{
          border: "1px solid var(--line)",
          borderRadius: 16,
          padding: 16,
          background: "var(--panel-strong)",
          display: "grid",
          gap: 6,
        }}
      >
        <strong>What happens next</strong>
        <span style={{ color: "var(--muted)", fontSize: 14 }}>
          The package begins in `processing`. Each uploaded PDF is checked for readability
          and page count, then the review workflow can be run from the packet page.
        </span>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={submitting || vendorName.trim().length === 0}
          style={{
            border: 0,
            borderRadius: 14,
            padding: "12px 18px",
            background: "var(--accent)",
            color: "white",
            cursor:
              submitting || vendorName.trim().length === 0 ? "not-allowed" : "pointer",
            opacity: submitting ? 0.7 : 1,
          }}
        >
          {submitting ? "Creating..." : "Create Packet"}
        </button>
        <a
          href="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            borderRadius: 14,
            padding: "12px 18px",
            background: "rgba(51, 44, 39, 0.08)",
            color: "var(--text)",
          }}
        >
          Back to Queue
        </a>
      </div>

      {statusMessage ? (
        <div style={{ color: "var(--danger)", fontSize: 14 }}>{statusMessage}</div>
      ) : null}
    </div>
  );
}

const inputStyle = {
  border: "1px solid var(--line)",
  borderRadius: 12,
  padding: "12px 14px",
  background: "white",
  color: "var(--text)",
  font: "inherit",
} as const;
