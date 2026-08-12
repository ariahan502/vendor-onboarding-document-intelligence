"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ReviewWorkspace } from "../../../components/review-workspace";
import { getPackageDetail } from "../../../lib/api";

export default function PackageDetailPage() {
  const { packageId } = useParams<{ packageId: string }>();
  const [packet, setPacket] = useState<Awaited<ReturnType<typeof getPackageDetail>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { getPackageDetail(packageId).then(setPacket).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Packet was not found.")); }, [packageId]);
  if (error) return <main className="state-shell"><div className="surface-card state-card"><h1 className="state-title">Packet unavailable</h1><p className="state-body">{error}</p></div></main>;
  if (!packet) return <main className="state-shell"><div className="surface-card state-card"><h1 className="state-title">Loading packet…</h1></div></main>;
  return <ReviewWorkspace packet={packet} />;
}
