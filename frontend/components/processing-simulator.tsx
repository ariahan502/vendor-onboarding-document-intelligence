"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { postProcessQueuedPackage } from "../lib/api";

type ProcessingSimulatorProps = {
  packageId: string;
  packageStatus: string;
  processingStateLabel: string;
};

export function ProcessingSimulator({
  packageId,
  packageStatus,
  processingStateLabel,
}: ProcessingSimulatorProps) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const canSimulate =
    packageStatus === "processing" || processingStateLabel === "In Progress";

  if (!canSimulate) {
    return null;
  }

  async function handleSimulate() {
    try {
      setSubmitting(true);
      setStatusMessage(null);
      const result = await postProcessQueuedPackage(packageId);
      setStatusMessage(
        `Processing completed: ${result.package_status.replaceAll("_", " ")} with ${
          result.finding_count
        } finding${result.finding_count === 1 ? "" : "s"}.`,
      );
      router.refresh();
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Failed to simulate processing.",
      );
    } finally {
      setSubmitting(false);
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
      <div style={{ display: "grid", gap: 4 }}>
        <strong style={{ fontSize: 16 }}>Queued Processing</strong>
        <span style={{ color: "var(--muted)", fontSize: 14 }}>
          This packet is waiting for the worker. Run it once locally, or use the background
          worker service when running Docker Compose.
        </span>
      </div>

      <button
        type="button"
        onClick={handleSimulate}
        disabled={submitting}
        style={{
          border: 0,
          borderRadius: 14,
          padding: "12px 16px",
          background: "var(--accent)",
          color: "white",
          cursor: submitting ? "not-allowed" : "pointer",
          opacity: submitting ? 0.7 : 1,
        }}
      >
        {submitting ? "Running Worker..." : "Run Queued Processing"}
      </button>

      {statusMessage ? (
        <div style={{ color: "var(--muted)", fontSize: 13 }}>{statusMessage}</div>
      ) : null}
    </div>
  );
}
