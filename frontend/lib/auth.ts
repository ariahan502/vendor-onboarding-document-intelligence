"use client";

type AccessTokenProvider = () => Promise<string | null>;

let accessTokenProvider: AccessTokenProvider | null = null;

export function setAccessTokenProvider(provider: AccessTokenProvider | null) {
  accessTokenProvider = provider;
}

export async function authorizationHeaders(): Promise<Record<string, string>> {
  const token = await accessTokenProvider?.();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
