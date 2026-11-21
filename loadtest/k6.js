// SETHU load test (k6). docs/LOAD-AND-DRILLS.md has how to run it and the results.
//
// Runs inside the Compose project's networks against the backend and Keycloak directly, so the edge's
// per-address rate limits (which would turn one load generator into one very busy "user") are not measured
// here; the edge is measured separately. Mock data only: run after `python seed/volume.py 100000`.
//
//   SETHU_BASE      backend, default http://backend:8000
//   SETHU_KC        Keycloak, default http://keycloak:8080
//   SETHU_PUBLIC    the stack's public address (redirect URI and issuer), default http://localhost:8080
//   DEMO_USER_PASSWORD  the dev demo users' password (from .env; never committed)
//   USERS (50), DURATION (5m), INTAKE_RATE (20 per second at the peak of each burst)
import http from "k6/http";
import { check, sleep } from "k6";
import crypto from "k6/crypto";
import encoding from "k6/encoding";
import { Trend } from "k6/metrics";

const BASE = __ENV.SETHU_BASE || "http://backend:8000";
const KC = __ENV.SETHU_KC || "http://keycloak:8080";
const PUBLIC = __ENV.SETHU_PUBLIC || "http://localhost:8080";
const PASSWORD = __ENV.DEMO_USER_PASSWORD || "";
const USERS = parseInt(__ENV.USERS || "50", 10);
const DURATION = __ENV.DURATION || "5m";
const RATE = parseInt(__ENV.INTAKE_RATE || "20", 10);
const OIDC = "/auth/realms/sethu/protocol/openid-connect";
const PEOPLE = ["rao", "fernandes", "iyer", "menon", "admin", "das"];
const CATEGORIES = ["Fee refund", "Infrastructure", "Examination", "Ragging", "Scholarship delay"];
const STATES = ["Karnataka", "Tamil Nadu", "Maharashtra", "Gujarat"];

const screen = new Trend("sethu_screen_ms", true); // per screen, tagged with its name

export const options = {
  scenarios: {
    officers: { // people sign in over two minutes (as a morning does), then all stay busy for DURATION
      executor: "ramping-vus", exec: "officer", startVUs: 0,
      stages: [{ target: USERS, duration: "2m" }, { target: USERS, duration: DURATION }] },
    intake: {
      executor: "ramping-arrival-rate", exec: "intake", startRate: 0, timeUnit: "1s",
      preAllocatedVUs: 20, maxVUs: 60, startTime: "150s",
      stages: [ // two bursts of 30 seconds, a quiet minute between
        { target: RATE, duration: "10s" }, { target: RATE, duration: "30s" }, { target: 0, duration: "10s" },
        { target: 0, duration: "60s" },
        { target: RATE, duration: "10s" }, { target: RATE, duration: "30s" }, { target: 0, duration: "10s" },
      ],
    },
    detector: { executor: "constant-arrival-rate", exec: "detector", rate: 1, timeUnit: "1m",
                duration: DURATION, preAllocatedVUs: 1, startTime: "20s" },
  },
  summaryTrendStats: ["min", "med", "p(95)", "p(99)", "max", "count"],
};

const b64url = (bytes) => encoding.b64encode(bytes, "rawurl");
const unescape = (s) => s.replace(/&amp;/g, "&");
const internal = (url) => url.replace(`${PUBLIC}/auth`, `${KC}/auth`);

// The browser's sign-in: authorization code with PKCE through Keycloak's own form.
function signIn(user) {
  const jar = http.cookieJar();
  jar.clear(KC);
  const verifier = b64url(crypto.randomBytes(32));
  const challenge = crypto.sha256(verifier, "base64rawurl");
  const query = `client_id=sethu-web&response_type=code&scope=openid&state=${b64url(crypto.randomBytes(8))}` +
    `&redirect_uri=${encodeURIComponent(PUBLIC + "/")}&code_challenge=${challenge}&code_challenge_method=S256`;
  const form = http.get(`${KC}${OIDC}/auth?${query}`, { tags: { name: "kc_form" } });
  const action = (form.body || "").match(/action="([^"]+)"/);
  if (!action) throw new Error(`no sign-in form (${form.status})`);
  const posted = http.post(internal(unescape(action[1])), { username: user, password: PASSWORD, credentialId: "" },
                           { redirects: 0, tags: { name: "kc_login" } });
  const code = ((posted.headers.Location || "").match(/[?&]code=([^&]+)/) || [])[1];
  if (!code) throw new Error(`sign-in refused for ${user} (${posted.status})`);
  return tokens({ grant_type: "authorization_code", code, code_verifier: verifier, redirect_uri: PUBLIC + "/" });
}

function tokens(params) {
  const r = http.post(`${KC}${OIDC}/token`, Object.assign({ client_id: "sethu-web" }, params),
                      { tags: { name: "kc_token" } });
  if (r.status !== 200) return null;
  const t = r.json();
  return { access: t.access_token, refresh: t.refresh_token, at: Date.now() };
}

function get(session, path, name) {
  const r = http.get(`${BASE}/api/v1${path}`, { headers: { Authorization: `Bearer ${session.access}` }, tags: { name } });
  screen.add(r.timings.duration, { screen: name });
  check(r, { [`${name} 200`]: (x) => x.status === 200 });
  return r;
}

const pick = (list) => list[Math.floor(Math.random() * list.length)];
let me = null; // one signed-in person per virtual user, as in the browser

export function officer() {
  if (!me) me = { user: PEOPLE[(__VU - 1) % PEOPLE.length], session: signIn(PEOPLE[(__VU - 1) % PEOPLE.length]) };
  if (Date.now() - me.session.at > 240_000) {  // access tokens last 5 minutes; the web refreshes too
    me.session = tokens({ grant_type: "refresh_token", refresh_token: me.session.refresh }) || signIn(me.user);
  }
  const s = me.session;
  const roll = Math.random();
  if (roll < 0.15) get(s, "/dashboard", "dashboard");
  else if (roll < 0.40) {
    const filter = pick(["", `?category=${encodeURIComponent(pick(CATEGORIES))}`, "?status=open",
                         `?state=${encodeURIComponent(pick(STATES))}`, "?overdue=true", "?offset=200"]);
    const list = get(s, `/cases${filter}`, "cases");
    const rows = list.status === 200 ? list.json().items : [];
    if (rows.length) get(s, `/cases/${pick(rows).id}`, "case");
  } else if (roll < 0.55) get(s, `/search?q=${encodeURIComponent(pick(["greenfield", "refund", "hostel fees", "LT-0042"]))}`, "search");
  else if (roll < 0.63) get(s, "/overlaps?status=proposed", "overlaps");
  else if (roll < 0.70) get(s, "/alerts", "alerts");
  else if (roll < 0.76) get(s, "/findings", "findings");
  else if (roll < 0.84) get(s, `/graph?state=${encodeURIComponent(pick(STATES))}`, "graph");
  else if (roll < 0.90) get(s, `/institutions?q=${pick(["inst", "college", "tech"])}`, "institutions");
  else if (roll < 0.95) get(s, "/cases/mine", "mine");
  else get(s, pick(["/reports/bureaus", "/reports/institutions"]), "report");
  sleep(1 + Math.random() * 2); // think time
}

// setup: an API key for the load-test source, with its per-minute quota raised for the bursts.
export function setup() {
  if (!PASSWORD) throw new Error("set DEMO_USER_PASSWORD");
  const admin = signIn("admin");
  const auth = { headers: { Authorization: `Bearer ${admin.access}`, "Content-Type": "application/json" } };
  let source = http.get(`${BASE}/api/v1/intake/sources`, auth).json().find((x) => x.name === "load-test-api");
  if (!source) {
    source = http.post(`${BASE}/api/v1/intake/sources`,
      JSON.stringify({ name: "load-test-api", channel: "api", bureau: "PGRC", priority: 1 }), auth).json();
  }
  http.patch(`${BASE}/api/v1/intake/sources/${source.id}`, JSON.stringify({ rate_per_minute: 10000 }), auth);
  const key = http.post(`${BASE}/api/v1/intake/sources/${source.id}/key`, null, auth).json();
  return { key: key.api_key, admin: admin.refresh };
}

export function intake(data) {
  const n = `${__VU}-${__ITER}-${Date.now()}`;
  const r = http.post(`${BASE}/api/v1/intake/submissions`, JSON.stringify({
    institution_name: pick(["Greenfield Institute of Technology", "Greenfeild Inst. of Technology", "Riverside College"]),
    category: pick(CATEGORIES),
    body: `Load test intake ${n}: the hostel deposit and the examination fees were not refunded after requests.`,
    external_ref: `lt-${n}`,
  }), { headers: { "Content-Type": "application/json", "X-Sethu-Key": data.key,
                   "X-Sethu-Timestamp": `${Math.floor(Date.now() / 1000)}`, "X-Sethu-Nonce": b64url(crypto.randomBytes(18)) },
        tags: { name: "intake" } });
  screen.add(r.timings.duration, { screen: "intake" });
  check(r, { "intake 202": (x) => x.status === 202 });
}

// The overlap detector, queued to the worker once a minute (as the admin's button does), alongside the
// scheduled jobs the worker runs anyway.
let adminSession = null;
export function detector(data) {
  adminSession = (adminSession && tokens({ grant_type: "refresh_token", refresh_token: adminSession.refresh }))
    || tokens({ grant_type: "refresh_token", refresh_token: data.admin }) || signIn("admin");
  const r = http.post(`${BASE}/api/v1/overlaps/detect`, null,
                      { headers: { Authorization: `Bearer ${adminSession.access}` }, tags: { name: "detect" } });
  check(r, { "detect 202": (x) => x.status === 202 });
}

export function handleSummary(data) {
  return { stdout: JSON.stringify(data.metrics, null, 1), "/out/summary.json": JSON.stringify(data, null, 1) };
}
