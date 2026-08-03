import Link from "next/link";

export default function NotFound() {
  return (
    <main className="state-shell">
      <section className="hero-card state-card">
        <span className="state-eyebrow">Not Found</span>
        <h1 className="state-title">This vendor packet does not exist</h1>
        <p className="state-body">
          The requested package could not be found. It may have been removed, or
          the packet ID may be invalid.
        </p>
        <div className="state-actions">
          <Link className="state-button" href="/">
            Return to package queue
          </Link>
        </div>
      </section>
    </main>
  );
}
