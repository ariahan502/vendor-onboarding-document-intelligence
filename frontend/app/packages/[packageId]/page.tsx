import { notFound } from "next/navigation";

import { ReviewWorkspace } from "../../../components/review-workspace";
import { getPackageDetail } from "../../../lib/api";

type PageProps = {
  params: Promise<{ packageId: string }>;
};

export default async function PackageDetailPage({ params }: PageProps) {
  const { packageId } = await params;
  const packet = await getPackageDetail(packageId).catch(() => null);

  if (!packet) {
    notFound();
  }

  return <ReviewWorkspace packet={packet} />;
}
