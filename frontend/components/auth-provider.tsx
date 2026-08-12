"use client";

import { InteractionStatus, PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider, useIsAuthenticated, useMsal } from "@azure/msal-react";
import { useState, type ReactNode } from "react";

import { setAccessTokenProvider } from "../lib/auth";

const clientId = process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID;
const tenantId = process.env.NEXT_PUBLIC_ENTRA_TENANT_ID;
const apiScope = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE;
const authEnabled = Boolean(clientId && tenantId && apiScope);
const msal = authEnabled
  ? new PublicClientApplication({
      auth: { clientId: clientId!, authority: `https://login.microsoftonline.com/${tenantId}`, redirectUri: typeof window === "undefined" ? undefined : window.location.origin },
      cache: { cacheLocation: "sessionStorage" },
    })
  : null;

export function AuthenticationProvider({ children }: { children: ReactNode }) {
  return msal ? <MsalProvider instance={msal}><AuthenticatedApp>{children}</AuthenticatedApp></MsalProvider> : <>{children}</>;
}

function AuthenticatedApp({ children }: { children: ReactNode }) {
  const { instance, accounts, inProgress } = useMsal();
  const authenticated = useIsAuthenticated();
  const account = accounts[0];
  const [signInError, setSignInError] = useState<string | null>(null);
  setAccessTokenProvider(async () => {
    if (!account || !apiScope) return null;
    const result = await instance.acquireTokenSilent({ account, scopes: [apiScope] });
    return result.accessToken;
  });
  if (!authenticated || !account) {
    const signingIn = inProgress !== InteractionStatus.None;
    async function signIn() {
      if (signingIn) return;
      setSignInError(null);
      try {
        await instance.loginPopup({ scopes: [apiScope!] });
      } catch (error) {
        setSignInError(error instanceof Error ? error.message : "Microsoft sign-in could not be completed.");
      }
    }
    return <main className="state-shell"><div className="surface-card state-card"><span className="state-eyebrow">Protected demo</span><h1 className="state-title">Sign in to review packets</h1><p className="state-body">This deployment uses Microsoft Entra ID. Only users assigned an application role can access vendor packet data.</p><button className="state-button" disabled={signingIn} onClick={signIn}>{signingIn ? "Signing in…" : "Sign in with Microsoft"}</button>{signInError ? <p className="state-body" style={{ color: "var(--danger)" }}>{signInError}</p> : null}</div></main>;
  }
  return <>{children}</>;
}
