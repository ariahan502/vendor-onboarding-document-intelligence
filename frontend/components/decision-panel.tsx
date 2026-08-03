"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { postReviewDecision } from "../lib/api";

type DecisionPanelProps = {
  packageId: string;
  systemRecommendation: string | null;
  notes: string | null;
  openHighRiskFindings: string[];
};

const ACTIONS = [
  { label: "Approve", value: "approve", tone: "ok" },
  { label: "Needs Review", value: "needs_review", tone: "warn" },
  { label: "Request Resubmission", value: "request_resubmission", tone: "neutral" },
  { label: "Escalate", value: "escalate", tone: "danger" },
] as const;

export function DecisionPanel({
  packageId,
  systemRecommendation,
  notes,
  openHighRiskFindings,
}: DecisionPanelProps) {
  const router = useRouter();
  const [reviewer, setReviewer] = useState("aria.han");
  const [comment, setComment] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<string | null>(null);

  async function handleSubmit(finalDecision: string) {
    try {
      setSubmitting(finalDecision);
      setStatusMessage(null);
      await postReviewDecision(packageId, {
        reviewer,
        final_decision: finalDecision,
        reviewer_comment: comment || null,
        override_reason:
          finalDecision === "approve" && openHighRiskFindings.length > 0
            ? overrideReason || null
            : finalDecision !== systemRecommendation
              ? overrideReason || "Reviewer selected a different final decision."
              : null,
      });
      setStatusMessage(`Saved decision: ${finalDecision.replaceAll("_", " ")}.`);
      router.refresh();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to submit review decision.";
      setStatusMessage(message);
    } finally {
      setSubmitting(null);
    }
  }

  return (
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
      <div>
        <div style={{ color: "var(--muted)", fontSize: 13 }}>System recommendation</div>
        <div style={{ marginTop: 4 }}>
          <StatusChip
            label={systemRecommendation ?? "pending"}
            tone={recommendationTone(systemRecommendation)}
          />
        </div>
      </div>

      <div style={{ color: "var(--muted)", fontSize: 14 }}>
        {notes ?? "Add a reviewer decision and note to move this packet forward."}
      </div>

      <label style={{ display: "grid", gap: 6 }}>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>Reviewer</span>
        <input
          value={reviewer}
          onChange={(event) => setReviewer(event.target.value)}
          placeholder="reviewer id"
          style={inputStyle}
        />
      </label>

      {openHighRiskFindings.length > 0 ? (
        <label style={{ display: "grid", gap: 6 }}>
          <span style={{ fontSize: 13, color: "var(--warn)" }}>
            Approval override reason required: {openHighRiskFindings.join("; ")}
          </span>
          <textarea
            value={overrideReason}
            onChange={(event) => setOverrideReason(event.target.value)}
            placeholder="Explain why approval is safe despite the remaining high-risk finding."
            rows={3}
            style={{ ...inputStyle, resize: "vertical" }}
          />
        </label>
      ) : null}

      <label style={{ display: "grid", gap: 6 }}>
        <span style={{ fontSize: 13, color: "var(--muted)" }}>Reviewer note</span>
        <textarea
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Add context for the final decision."
          rows={4}
          style={{ ...inputStyle, resize: "vertical" }}
        />
      </label>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {ACTIONS.map((action) => (
          <button
            key={action.value}
            type="button"
            onClick={() => handleSubmit(action.value)}
            disabled={
              submitting !== null ||
              reviewer.trim().length === 0 ||
              (action.value === "approve" &&
                openHighRiskFindings.length > 0 &&
                overrideReason.trim().length < 3)
            }
            style={{
              ...actionButtonStyles[action.tone],
              opacity: submitting !== null && submitting !== action.value ? 0.5 : 1,
              cursor:
                submitting !== null ||
                reviewer.trim().length === 0 ||
                (action.value === "approve" &&
                  openHighRiskFindings.length > 0 &&
                  overrideReason.trim().length < 3)
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {submitting === action.value ? "Saving..." : action.label}
          </button>
        ))}
      </div>

      {statusMessage ? (
        <div style={{ fontSize: 13, color: "var(--muted)" }}>{statusMessage}</div>
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

const actionButtonStyles = {
  neutral: {
    border: 0,
    borderRadius: 14,
    padding: "12px 14px",
    background: "rgba(51, 44, 39, 0.08)",
    color: "var(--text)",
  },
  danger: {
    border: 0,
    borderRadius: 14,
    padding: "12px 14px",
    background: "var(--danger)",
    color: "white",
  },
  warn: {
    border: 0,
    borderRadius: 14,
    padding: "12px 14px",
    background: "var(--accent)",
    color: "white",
  },
  ok: {
    border: 0,
    borderRadius: 14,
    padding: "12px 14px",
    background: "var(--ok)",
    color: "white",
  },
} as const;

function StatusChip({
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
