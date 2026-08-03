import Link from "next/link";

import { EmptyState } from "../components/empty-state";
import { getPackageQueue } from "../lib/api";
import { formatDateTime } from "../lib/format";
import type { PackageQueueItem } from "../types/packages";

export default async function HomePage() {
  const queue = await getPackageQueue();
  const orderedItems = [...queue.items].sort(compareQueuePriority);
  const openItems = orderedItems.filter((item) => !isResolved(item.package_status));
  const resolvedItems = orderedItems.filter((item) => isResolved(item.package_status));
  const openHighRiskFindings = openItems.reduce(
    (total, item) =>
      total + (item.highest_severity === "high" || item.highest_severity === "critical" ? 1 : 0),
    0,
  );
  const ocrBlockedPackets = openItems.filter(
    (item) => item.ocr_required_document_count > 0,
  ).length;
  const decidedItems = orderedItems.filter((item) => item.final_decision !== null);
  const overrideRate = decidedItems.length
    ? Math.round(
        (decidedItems.filter(
          (item) =>
            item.recommendation_status !== null &&
            item.final_decision !== item.recommendation_status,
        ).length /
          decidedItems.length) *
          100,
      )
    : 0;
  const averageReviewAgeDays = openItems.length
    ? Math.round(
        (openItems.reduce(
          (total, item) => total + (Date.now() - new Date(item.submission_date).getTime()),
          0,
        ) /
          openItems.length /
          86_400_000) *
          10,
      ) / 10
    : 0;

  return (
    <main className="page-shell">
      <div className="page-frame">
        <section
          className="hero-card"
          style={{
            padding: 28,
            marginBottom: 24,
            display: "grid",
            gap: 16,
          }}
        >
          <div style={{ display: "grid", gap: 6 }}>
            <span
              style={{
                color: "var(--accent)",
                fontSize: 13,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
              }}
            >
              Vendor Onboarding Document Intelligence
            </span>
            <h1 style={{ margin: 0, fontSize: 42, lineHeight: 1.05 }}>
              Package Queue
            </h1>
            <p style={{ margin: 0, maxWidth: 760, color: "var(--muted)", fontSize: 18 }}>
              Review vendor packets, inspect document findings, and route cases with
              evidence-backed decisions instead of ad hoc manual checking.
            </p>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 6 }}>
              <Link
                href="/submit"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: "fit-content",
                  borderRadius: 14,
                  padding: "12px 16px",
                  background: "var(--accent)",
                  color: "white",
                }}
              >
                Create New Packet
              </Link>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: 12,
            }}
          >
            <MetricCard label="Open Work" value={String(openItems.length)} />
            <MetricCard label="Open High Risk" value={String(openHighRiskFindings)} />
            <MetricCard label="OCR Blocked" value={String(ocrBlockedPackets)} />
            <MetricCard
              label="Missing Documents"
              value={String(
                orderedItems.filter((item) => item.missing_required_documents.length > 0).length,
              )}
            />
            <MetricCard
              label="Average Review Age"
              value={`${averageReviewAgeDays}d`}
            />
            <MetricCard label="Decision Override Rate" value={`${overrideRate}%`} />
          </div>
        </section>

        <section className="surface-card" style={{ padding: 20, display: "grid", gap: 18 }}>
          {orderedItems.length === 0 ? (
            <EmptyState
              eyebrow="Queue"
              title="No vendor packets are waiting for review"
              body="Once onboarding packets are submitted or seeded into the system, they will appear here for procurement or finance reviewers."
            />
          ) : (
            <>
              <QueueSection
                title="Action Queue"
                subtitle="Packets that still need reviewer attention, escalation, or resubmission."
                items={openItems}
              />
              {resolvedItems.length > 0 ? (
                <QueueSection
                  title="Recently Decided"
                  subtitle="Packets that already have a human outcome recorded."
                  items={resolvedItems}
                />
              ) : null}
            </>
          )}
        </section>
      </div>
    </main>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: "var(--panel-strong)",
        border: "1px solid var(--line)",
        borderRadius: 18,
        padding: 16,
      }}
    >
      <div style={{ color: "var(--muted)", fontSize: 13 }}>{label}</div>
      <div style={{ marginTop: 8, fontSize: 30, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function QueueSection({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: PackageQueueItem[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "grid", gap: 4 }}>
        <strong style={{ fontSize: 20 }}>{title}</strong>
        <span style={{ color: "var(--muted)", fontSize: 14 }}>{subtitle}</span>
      </div>

      <div style={{ display: "grid", gap: 12 }}>
        {items.map((item) => (
          <Link
            key={item.package_id}
            href={`/packages/${item.package_id}`}
            style={{
              border: "1px solid var(--line)",
              borderRadius: 20,
              padding: 18,
              background: "var(--panel-strong)",
              display: "grid",
              gap: 14,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 16,
                flexWrap: "wrap",
                alignItems: "flex-start",
              }}
            >
              <div style={{ display: "grid", gap: 5 }}>
                <strong style={{ fontSize: 18 }}>{item.vendor_name}</strong>
                <span style={{ color: "var(--muted)", fontSize: 13 }}>
                  {item.package_id} • Submitted {formatDateTime(item.submission_date)}
                </span>
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <SeverityPill tone={packageTone(item.package_status)} label={item.package_status} />
                <SeverityPill
                  tone={recommendationTone(item.recommendation_status)}
                  label={item.recommendation_status ?? "pending"}
                />
                {item.final_decision ? (
                  <SeverityPill
                    tone={recommendationTone(item.final_decision)}
                    label={`final: ${item.final_decision}`}
                  />
                ) : null}
                {item.primary_finding_type ? (
                  <SeverityPill
                    tone={findingTone(item.highest_severity)}
                    label={findingLabel(item.primary_finding_type)}
                  />
                ) : null}
              </div>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: 10,
              }}
            >
              <QueueStat label="Findings" value={String(item.finding_count)} />
              <QueueStat label="Highest Severity" value={item.highest_severity ?? "none"} />
              <QueueStat label="Reviewer" value={item.assigned_reviewer ?? "unassigned"} />
              <QueueStat
                label="Missing Docs"
                value={String(item.missing_required_documents.length)}
              />
            </div>

            <div style={{ display: "grid", gap: 6 }}>
              <span style={{ color: "var(--muted)", fontSize: 13 }}>Primary blocker</span>
              <span style={{ fontSize: 15 }}>{queueBlockerText(item)}</span>
            </div>

            {item.latest_reviewer_comment ? (
              <div
                style={{
                  borderTop: "1px solid var(--line)",
                  paddingTop: 12,
                  display: "grid",
                  gap: 4,
                }}
              >
                <span style={{ color: "var(--muted)", fontSize: 13 }}>
                  Latest reviewer note
                  {item.latest_decision_at ? ` • ${formatDateTime(item.latest_decision_at)}` : ""}
                </span>
                <span style={{ fontSize: 14 }}>{item.latest_reviewer_comment}</span>
              </div>
            ) : null}
          </Link>
        ))}
      </div>
    </div>
  );
}

function QueueStat({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        border: "1px solid var(--line)",
        borderRadius: 14,
        padding: 12,
        background: "rgba(255, 255, 255, 0.5)",
        display: "grid",
        gap: 4,
      }}
    >
      <span style={{ color: "var(--muted)", fontSize: 12 }}>{label}</span>
      <strong style={{ fontSize: 15, textTransform: "capitalize" }}>
        {value.replaceAll("_", " ")}
      </strong>
    </div>
  );
}

function SeverityPill({
  label,
  tone,
}: {
  label: string;
  tone: "neutral" | "danger" | "warn" | "ok";
}) {
  const colors = {
    neutral: {
      bg: "rgba(51, 44, 39, 0.08)",
      text: "var(--text)",
    },
    danger: {
      bg: "rgba(170, 59, 47, 0.14)",
      text: "var(--danger)",
    },
    warn: {
      bg: "rgba(139, 90, 20, 0.14)",
      text: "var(--warn)",
    },
    ok: {
      bg: "rgba(47, 108, 85, 0.14)",
      text: "var(--ok)",
    },
  }[tone];

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "fit-content",
        borderRadius: 999,
        padding: "6px 10px",
        background: colors.bg,
        color: colors.text,
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

function packageTone(status: string) {
  if (status === "approved") return "ok";
  if (status === "escalated" || status === "rejected") return "danger";
  if (status === "ready_for_review" || status === "needs_vendor_resubmission") return "warn";
  return "neutral";
}

function findingTone(severity: string | null) {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warn";
  return "neutral";
}

function findingLabel(type: string) {
  const labels: Record<string, string> = {
    missing_document: "missing document",
    cross_document_mismatch: "document mismatch",
    data_gap: "data needed",
    policy_violation: "policy check",
    confidence_check: "verify details",
  };
  return labels[type] ?? type.replaceAll("_", " ");
}

function isResolved(status: string) {
  return status === "approved" || status === "rejected";
}

function compareQueuePriority(a: PackageQueueItem, b: PackageQueueItem) {
  return queuePriority(b) - queuePriority(a);
}

function queuePriority(item: PackageQueueItem) {
  let score = 0;
  if (item.package_status === "escalated") score += 50;
  if (item.missing_required_documents.length > 0) score += 30;
  if (item.highest_severity === "critical") score += 25;
  if (item.highest_severity === "high") score += 20;
  if (item.package_status === "ready_for_review") score += 15;
  score += item.finding_count;
  if (item.final_decision) score -= 40;
  return score;
}

function queueBlockerText(item: PackageQueueItem) {
  if (item.missing_required_documents.length > 0) {
    return `Missing required docs: ${item.missing_required_documents.join(", ")}.`;
  }
  if (item.primary_finding_title) {
    return item.primary_finding_title;
  }
  if (item.highest_severity === "high" || item.highest_severity === "critical") {
    return "High-risk finding requires reviewer judgment before onboarding can proceed.";
  }
  if (item.final_decision) {
    return `Human decision recorded as ${item.final_decision.replaceAll("_", " ")}.`;
  }
  if (item.recommendation_status) {
    return `System is recommending ${item.recommendation_status.replaceAll("_", " ")}.`;
  }
  return "Packet is still moving through processing and review.";
}
