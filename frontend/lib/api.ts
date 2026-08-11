import type {
  PackageCreateRequest,
  PackageCreateResponse,
  DocumentUploadResponse,
  FieldReviewOverrideCreateRequest,
  FieldReviewOverrideCreateResponse,
  FindingResolutionCreateRequest,
  FindingResolutionCreateResponse,
  PackageDetailResponse,
  PackageQueueResponse,
  PackageSimulationResponse,
  ReviewDecisionCreateRequest,
  ReviewDecisionCreateResponse,
} from "../types/packages";
import { authorizationHeaders } from "./auth";

const DEFAULT_API_BASE = "http://localhost:8000/api";

function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE;
}

export async function getPackageQueue(): Promise<PackageQueueResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/`, {
    cache: "no-store",
    headers: await authorizationHeaders(),
  });

  if (!response.ok) {
    throw new Error("Failed to load package queue.");
  }

  return response.json();
}

export async function getPackageDetail(
  packageId: string,
): Promise<PackageDetailResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}`, {
    cache: "no-store",
    headers: await authorizationHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to load package '${packageId}'.`);
  }

  return response.json();
}

export async function postCreatePackage(
  payload: PackageCreateRequest,
): Promise<PackageCreateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authorizationHeaders()),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to create onboarding package.");
  }

  return response.json();
}

export async function postUploadDocument(
  packageId: string,
  docType: string,
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("doc_type", docType);
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/documents`, {
    method: "POST",
    headers: await authorizationHeaders(), body: formData,
  });

  if (!response.ok) {
    const message = await response.json().catch(() => null);
    throw new Error(message?.detail ?? `Failed to upload ${file.name}.`);
  }

  return response.json();
}

export async function postFieldReviewOverride(
  packageId: string,
  payload: FieldReviewOverrideCreateRequest,
): Promise<FieldReviewOverrideCreateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/field-overrides`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authorizationHeaders()) },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.json().catch(() => null);
    throw new Error(message?.detail ?? "Failed to save reviewer correction.");
  }

  return response.json();
}

export async function postFindingResolution(
  packageId: string,
  payload: FindingResolutionCreateRequest,
): Promise<FindingResolutionCreateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/finding-resolutions`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authorizationHeaders()) },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.json().catch(() => null);
    throw new Error(message?.detail ?? "Failed to save finding resolution.");
  }

  return response.json();
}

export function getDocumentUrl(filePath: string) {
  if (filePath.startsWith("http://") || filePath.startsWith("https://")) {
    return filePath;
  }
  if (filePath.startsWith("/api/")) {
    return `${getApiBaseUrl().replace(/\/api$/, "")}${filePath}`;
  }
  return filePath;
}

export async function postReviewDecision(
  packageId: string,
  payload: ReviewDecisionCreateRequest,
): Promise<ReviewDecisionCreateResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/decisions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authorizationHeaders()),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Failed to submit decision for package '${packageId}'.`);
  }

  return response.json();
}

export async function postSimulateProcessing(
  packageId: string,
): Promise<PackageSimulationResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/simulate-processing`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authorizationHeaders()),
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to simulate processing for package '${packageId}'.`);
  }

  return response.json();
}

export async function postProcessQueuedPackage(
  packageId: string,
): Promise<PackageSimulationResponse> {
  const response = await fetch(`${getApiBaseUrl()}/packages/${packageId}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authorizationHeaders()) },
  });

  if (!response.ok) {
    throw new Error(`Failed to process queued package '${packageId}'.`);
  }

  return response.json();
}
