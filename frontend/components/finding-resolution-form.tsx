"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { postFindingResolution } from "../lib/api";
import type { FindingResolutionCreateRequest } from "../types/packages";

type FindingResolutionFormProps = {
  packageId: string;
  findingId: string;
};

export function FindingResolutionForm({ packageId, findingId }: FindingResolutionFormProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [reviewer, setReviewer] = useState("aria.han");
  const [status, setStatus] = useState<FindingResolutionCreateRequest["resolution_status"]>("resolved");
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function submit() {
    try {
      setSaving(true);
      setMessage(null);
      await postFindingResolution(packageId, {
        finding_id: findingId,
        reviewer,
        resolution_status: status,
        resolution_note: note,
      });
      setIsOpen(false);
      setMessage("Finding resolution saved.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to save resolution.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 8, marginTop: 4 }}>
      <button type="button" onClick={() => setIsOpen((value) => !value)} style={buttonStyle}>
        {isOpen ? "Cancel resolution" : "Resolve finding"}
      </button>
      {isOpen ? (
        <div style={{ display: "grid", gap: 8 }}>
          <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} placeholder="Reviewer" style={inputStyle} />
          <select value={status} onChange={(event) => setStatus(event.target.value as FindingResolutionCreateRequest["resolution_status"])} style={inputStyle}>
            <option value="resolved">Resolved</option>
            <option value="accepted_risk">Accepted risk</option>
            <option value="not_applicable">Not applicable</option>
          </select>
          <textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Explain how this finding was handled." rows={3} style={{ ...inputStyle, resize: "vertical" }} />
          <button type="button" onClick={submit} disabled={saving || !reviewer.trim() || note.trim().length < 3} style={{ ...buttonStyle, background: "var(--accent)", color: "white" }}>
            {saving ? "Saving..." : "Save resolution"}
          </button>
        </div>
      ) : null}
      {message ? <span style={{ color: "var(--muted)", fontSize: 13 }}>{message}</span> : null}
    </div>
  );
}

const inputStyle = { border: "1px solid var(--line)", borderRadius: 10, padding: "9px 10px", background: "white", color: "var(--text)", font: "inherit" } as const;
const buttonStyle = { border: "1px solid var(--line)", borderRadius: 10, padding: "8px 10px", background: "rgba(51, 44, 39, 0.06)", color: "var(--text)", cursor: "pointer", font: "inherit", width: "fit-content" } as const;
