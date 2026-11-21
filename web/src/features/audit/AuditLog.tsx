import { useState } from "react";
import { api, useLoad } from "../../api";

// Mirrors backend/app/modules/audit_view/schemas.py
type Entry = {
  seq: number;
  ts: string;
  actor: string;
  actor_name: string;
  actor_role: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  payload: Record<string, unknown>;
  prev_hash: string;
  hash: string;
};
type EntryPage = { items: Entry[]; actions: string[] };
type ChainReport = { ok: boolean; checked: number; broken_seq: number | null; reason: string | null; row: Entry | null };

const PAGE = 50;
const EMPTY = { action: "", actor: "", entity_type: "", entity_id: "", date_from: "", date_to: "" };
const moment = (iso: string) => new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "medium" });
const target = (e: Entry) => [e.entity_type, e.entity_id].filter(Boolean).join(" ") || "—";

function Verify() {
  const [report, setReport] = useState<ChainReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setReport(await api<ChainReport>("/audit/verify"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request failed.");
    }
    setBusy(false);
  }

  return (
    <div>
      <button type="button" onClick={run} disabled={busy}>
        {busy ? "Verifying…" : "Verify chain"}
      </button>
      <div aria-live="polite">
        {error && <p role="alert">{error}</p>}
        {report?.ok && (
          <p role="status">
            Chain intact, {report.checked} entries. Every entry matches its hash and the one before it.
          </p>
        )}
        {report && !report.ok && (
          <div role="alert" className="overlap banner">
            <p>
              Chain broken at entry #{report.broken_seq}: {report.reason}. The {report.checked} entries before it are
              intact.
            </p>
            {report.row && (
              <dl>
                <dt>Entry #{report.row.seq} as stored now</dt>
                <dd>
                  {moment(report.row.ts)} · {report.row.actor_name} ({report.row.actor_role ?? "no role"}) ·{" "}
                  {report.row.action} · {target(report.row)}
                </dd>
                <dt>Payload</dt>
                <dd>
                  <code>{JSON.stringify(report.row.payload)}</code>
                </dd>
                <dt>Stored hash</dt>
                <dd>
                  <code>{report.row.hash}</code>
                </dd>
              </dl>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/** The hash-chained audit log, newest first. For auditor, oversight and admin. */
export function AuditLog() {
  const [draft, setDraft] = useState(EMPTY);
  const [filters, setFilters] = useState(EMPTY);
  const [older, setOlder] = useState<Entry[]>([]);
  const [more, setMore] = useState<{ done: boolean; error?: string }>({ done: false });
  const query = new URLSearchParams({ limit: String(PAGE) });
  Object.entries(filters).forEach(([k, v]) => v.trim() && query.set(k, v.trim()));
  const { data, error } = useLoad<EntryPage>(`/audit?${query}`);
  const items = [...(data?.items ?? []), ...older];

  function apply(next: typeof EMPTY) {
    setOlder([]);
    setMore({ done: false });
    setFilters(next);
  }

  async function loadOlder() {
    const q = new URLSearchParams(query);
    q.set("before_seq", String(items[items.length - 1].seq));
    try {
      const page = await api<EntryPage>(`/audit?${q}`);
      setOlder((o) => [...o, ...page.items]);
      setMore({ done: page.items.length < PAGE });
    } catch (e) {
      setMore({ done: false, error: e instanceof Error ? e.message : "The request failed." });
    }
  }

  const field = (label: string, name: keyof typeof EMPTY, type = "text") => (
    <label>
      {label}
      <input type={type} value={draft[name]} onChange={(e) => setDraft({ ...draft, [name]: e.target.value })} />
    </label>
  );

  return (
    <section>
      <h1>Audit log</h1>
      <p>
        Every change in SETHU, newest first. Entries are chained by hash, so editing, removing or reordering any past
        entry is detected by <strong>Verify chain</strong>. Entries hold identifiers and decisions, never complaint text.
      </p>
      <Verify />
      <form
        className="filters"
        onSubmit={(e) => {
          e.preventDefault();
          apply(draft);
        }}
      >
        <label>
          Action
          <select value={draft.action} onChange={(e) => setDraft({ ...draft, action: e.target.value })}>
            <option value="">Any</option>
            {[...new Set((data?.actions ?? []).map((a) => `${a.split(".")[0]}.`))].map((family) => (
              <option key={family} value={family}>
                {family}*
              </option>
            ))}
            {(data?.actions ?? []).map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        {field("Actor", "actor")}
        {field("Target type", "entity_type")}
        {field("Target id", "entity_id")}
        {field("From", "date_from", "date")}
        {field("To", "date_to", "date")}
        <button type="submit">Apply filters</button>
        <button type="button" onClick={() => (setDraft(EMPTY), apply(EMPTY))}>
          Clear
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      {data && items.length === 0 && <p>No entries match.</p>}
      {items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col" className="num">#</th>
              <th scope="col">Time</th>
              <th scope="col">Actor</th>
              <th scope="col">Action</th>
              <th scope="col">Target</th>
              <th scope="col">Hash</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.seq}>
                <td className="num">{e.seq}</td>
                <td>{moment(e.ts)}</td>
                <td>
                  {e.actor_name} <small>{e.actor_role}</small>
                </td>
                <td>{e.action}</td>
                <td>
                  <code>{target(e)}</code>
                </td>
                <td>
                  <code title={`hash ${e.hash}\nprevious ${e.prev_hash}`}>{e.hash.slice(0, 12)}…</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {more.error && <p role="alert">{more.error}</p>}
      {data && data.items.length === PAGE && !more.done && (
        <button type="button" onClick={loadOlder}>
          Older entries
        </button>
      )}
      <Anchors />
      <SignIns />
    </section>
  );
}

type SignIn = { time: string; type: string | null; username: string | null; client: string | null; ip: string | null; error: string | null };

/** Failed sign-ins, as Keycloak recorded them: read-only, kept by Keycloak for 90 days, not part of the chain. */
function SignIns() {
  const { data, error } = useLoad<SignIn[]>("/audit/signins");
  return (
    <>
      <h2>Failed sign-ins (from Keycloak)</h2>
      <p className="note">
        Read-only. These are Keycloak's own events, not entries of the hash-chained audit log; many failures for one
        name or from one address may be an attack.
      </p>
      {error && <p role="alert">{error}</p>}
      {data && data.length === 0 && <p>No failed sign-ins recorded.</p>}
      {data && data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Time</th><th scope="col">Event</th><th scope="col">Username</th>
              <th scope="col">Address</th><th scope="col">Reason</th>
            </tr>
          </thead>
          <tbody>
            {data.map((e) => (
              <tr key={`${e.time}${e.username}${e.ip}`}>
                <td>{new Date(e.time).toLocaleString()}</td>
                <td>{e.type}</td>
                <td>{e.username ?? "–"}</td>
                <td>{e.ip ?? "–"}</td>
                <td>{e.error ?? "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}

type AnchorReport = {
  configured: boolean;
  ok: boolean | null;
  anchors: number;
  problems: string[];
  live_entries: number | null;
  latest: { seq: number; hash: string; exported_at: string | null } | null;
};

/** The chain's exported anchors (outside the database) compared with the live chain. */
function Anchors() {
  const { data, error } = useLoad<AnchorReport>("/audit/anchor");
  return (
    <>
      <h2>Exported anchors</h2>
      <p className="note">
        Every hour the chain's latest entry and hash are appended to a write-once file outside the database. If the
        database were replaced or an entry rewritten, the live chain would no longer match.
      </p>
      {error && <p role="alert">{error}</p>}
      {data && !data.configured && <p>Not configured (SETHU_AUDIT_ANCHOR_DIR).</p>}
      {data?.configured && data.ok === null && <p>{data.problems[0] ?? "Nothing exported yet."}</p>}
      {data?.ok === true && data.latest && (
        <p role="status">
          All {data.anchors} exported anchors match the live chain. Latest: entry #{data.latest.seq}, exported{" "}
          {data.latest.exported_at ? new Date(data.latest.exported_at).toLocaleString() : "–"}; the chain now has{" "}
          {data.live_entries} entries.
        </p>
      )}
      {data?.ok === false && (
        <div role="alert" className="overlap banner">
          <p>The live chain does not match what was exported:</p>
          <ul>
            {data.problems.map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
