// Sign-in with Keycloak: authorization code flow with PKCE, same origin (/auth).
// Tokens are kept in memory only, so a page reload goes through Keycloak again
// (silent while the Keycloak session lasts).
const OIDC = "/auth/realms/sethu/protocol/openid-connect";
const CLIENT_ID = "sethu-web";
const PENDING = "sethu.login";

type Tokens = { access: string; refresh: string; expiresAt: number };
let tokens: Tokens | null = null;

const redirectUri = () => `${window.location.origin}/`;

function base64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function requestTokens(params: Record<string, string>): Promise<Tokens | null> {
  const response = await fetch(`${OIDC}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: CLIENT_ID, ...params }),
  });
  if (!response.ok) return null;
  const t = (await response.json()) as { access_token: string; refresh_token: string; expires_in: number };
  return { access: t.access_token, refresh: t.refresh_token, expiresAt: Date.now() + t.expires_in * 1000 };
}

async function login(): Promise<never> {
  const verifier = base64url(crypto.getRandomValues(new Uint8Array(32)));
  const state = base64url(crypto.getRandomValues(new Uint8Array(16)));
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  sessionStorage.setItem(PENDING, JSON.stringify({ verifier, state, hash: window.location.hash }));
  window.location.assign(
    `${OIDC}/auth?${new URLSearchParams({
      client_id: CLIENT_ID,
      redirect_uri: redirectUri(),
      response_type: "code",
      scope: "openid",
      state,
      code_challenge: base64url(new Uint8Array(digest)),
      code_challenge_method: "S256",
    })}`,
  );
  return new Promise<never>(() => {}); // the page is leaving
}

/** Call once before rendering. Finishes a sign-in redirect, or starts one. */
export async function start(): Promise<void> {
  const query = new URLSearchParams(window.location.search);
  const pending = JSON.parse(sessionStorage.getItem(PENDING) ?? "null") as
    | { verifier: string; state: string; hash: string }
    | null;
  sessionStorage.removeItem(PENDING);
  if (query.get("error")) throw new Error(`Sign-in was refused: ${query.get("error")}`);
  const code = query.get("code");
  if (code) {
    if (!pending || query.get("state") !== pending.state) throw new Error("Sign-in response did not match the request.");
    tokens = await requestTokens({
      grant_type: "authorization_code",
      code,
      redirect_uri: redirectUri(),
      code_verifier: pending.verifier,
    });
    // Stop here on failure: redirecting again could loop for ever.
    if (!tokens) throw new Error("Sign-in could not be completed.");
    window.history.replaceState(null, "", `/${pending.hash}`);
    return;
  }
  await login();
}

export async function accessToken(): Promise<string> {
  if (tokens && Date.now() > tokens.expiresAt - 30_000) {
    tokens = await requestTokens({ grant_type: "refresh_token", refresh_token: tokens.refresh });
  }
  return tokens ? tokens.access : login();
}

export function logout(): void {
  window.location.assign(
    `${OIDC}/logout?${new URLSearchParams({ client_id: CLIENT_ID, post_logout_redirect_uri: redirectUri() })}`,
  );
}
