"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { postFieldReviewOverride } from "../lib/api";

type FieldOverrideFormProps = {
  packageId: string;
  fieldId: string;
  originalValue: string | null;
};

export function FieldOverrideForm({
  packageId,
  fieldId,
  originalValue,
}: FieldOverrideFormProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [reviewer, setReviewer] = useState("aria.han");
  const [correctedValue, setCorrectedValue] = useState(originalValue ?? "");
  const [reason, setReason] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function submit() {
    try {
      setSaving(true);
      setStatusMessage(null);
      await postFieldReviewOverride(packageId, {
        field_id: fieldId,
        reviewer,
        corrected_value: correctedValue,
        correction_reason: reason,
      });
      setStatusMessage("Correction saved to the audit trail.");
      setIsOpen(false);
      router.refresh();
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Failed to save correction.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 8, marginTop: 4 }}>
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        style={buttonStyle}
      >
        {isOpen ? "Cancel correction" : "Correct field"}
      </button>
      {isOpen ? (
        <div style={{ display: "grid", gap: 8 }}>
          <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} placeholder="Reviewer" style={inputStyle} />
          <input value={correctedValue} onChange={(event) => setCorrectedValue(event.target.value)} placeholder="Corrected value" style={inputStyle} />
          <textarea value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Why is this correction needed?" style={{ ...inputStyle, minHeight: 70, resize: "vertical" }} />
          <button type="button" onClick={submit} disabled={saving || !reviewer.trim() || !correctedValue.trim() || reason.trim().length < 3} style={{ ...buttonStyle, background: "var(--accent)", color: "white" }}>
            {saving ? "Saving..." : "Save correction"}
          </button>
        </div>
      ) : null}
      {statusMessage ? <span style={{ color: "var(--muted)", fontSize: 13 }}>{statusMessage}</span> : null}
    </div>
  );
}

const inputStyle = {
  border: "1px solid var(--line)",
  borderRadius: 10,
  padding: "9px 10px",
  background: "white",
  color: "var(--text)",
  font: "inherit",
} as const;

const buttonStyle = {
  border: "1px solid var(--line)",
  borderRadius: 10,
  padding: "8px 10px",
  background: "rgba(51, 44, 39, 0.06)",
  color: "var(--text)",
  cursor: "pointer",
  font: "inherit",
  width: "fit-content",
} as const;
