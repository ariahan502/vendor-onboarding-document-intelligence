import Link from "next/link";

type EmptyStateProps = {
  eyebrow: string;
  title: string;
  body: string;
  actionLabel?: string;
  actionHref?: string;
};

export function EmptyState({
  eyebrow,
  title,
  body,
  actionLabel,
  actionHref,
}: EmptyStateProps) {
  return (
    <div
      style={{
        padding: 28,
        display: "grid",
        gap: 12,
        textAlign: "left",
      }}
    >
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
      <h2 style={{ margin: 0, fontSize: 30, lineHeight: 1.08 }}>{title}</h2>
      <p
        style={{
          margin: 0,
          color: "var(--muted)",
          fontSize: 16,
          lineHeight: 1.6,
          maxWidth: 680,
        }}
      >
        {body}
      </p>
      {actionLabel && actionHref ? (
        <Link
          href={actionHref}
          style={{
            display: "inline-flex",
            width: "fit-content",
            borderRadius: 14,
            padding: "12px 16px",
            background: "var(--accent)",
            color: "white",
          }}
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  );
}
