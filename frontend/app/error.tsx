"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="state-shell">
      <section className="hero-card state-card">
        <span className="state-eyebrow">Application Error</span>
        <h1 className="state-title">We couldn&apos;t load this screen</h1>
        <p className="state-body">
          Something went wrong while loading the vendor review experience. This is
          a good place to add API error handling and observability in the next
          iteration.
        </p>
        <p className="state-body" style={{ fontSize: 14 }}>
          {error.message}
        </p>
        <div className="state-actions">
          <button className="state-button" onClick={reset} type="button">
            Retry
          </button>
          <a className="state-button secondary" href="/">
            Back to queue
          </a>
        </div>
      </section>
    </main>
  );
}
