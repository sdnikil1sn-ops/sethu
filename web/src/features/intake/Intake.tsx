import { useState } from "react";
import { api, upload, useLoad } from "../../api";

// Mirrors backend/app/modules/intake/schemas.py
type Source = {
  id: string;
  name: string;
  channel: string;
  bureau: string;
  priority: number;
  fallback: string | null;
  active: boolean;
  marked_down: boolean;
  has_key: boolean;
  last_success_at: string | null;
  last_failure_at: string | null;
  failures: number;
  pending: number;
  dead: number;
};
type Item = {
  id: string;
  source: string;
  bureau: string;
  channel: string;
  path: string;
  status: string;
  attempts: number;
  next_attempt_at: string | null;
  last_error: string | null;
  ref: string | null;
  duplicate_of: string | null;
  near_duplicate_of: string | null;
  review_state: string | null;
  created_at: string;
  can_retry: boolean;
};
type RowError = { row: number; field: string; message: string };
type UploadResult = { accepted: number; rejected: number; errors: RowError[] };

const when = (t: string | null) => (t ? new Date(t).toLocaleString() : "never");
const ENTERS = ["officer", "bureau_head"];
const SEES_HEALTH = ["admin", "oversight", "auditor", "bureau_head"];

function saveErrors(errors: RowError[]) {
  // Row, field and rule only: the report never repeats what was in the file.
  const csv = ["row,field,message", ...errors.map((e) => `${e.row},${e.field},"${e.message.replace(/"/g, '""')}"`)];
  const url = URL.createObjectURL(new Blob([csv.join("\n") + "\n"], { type: "text/csv" }));
  Object.assign(document.createElement("a"), { href: url, download: "intake-errors.csv" }).click();
  URL.revokeObjectURL(url);
}

function ManualForm({ onDone }: { onDone: (message: string) => void }) {
  const empty = { institution_name: "", category: "", body: "", language: "en", name: "", email: "", phone: "" };
  const [f, setF] = useState(empty);
  const set = (k: keyof typeof empty) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const person = { name: f.name.trim(), email: f.email.trim() || null, phone: f.phone.trim() || null };
    try {
      await api("/intake/manual", {
        institution_name: f.institution_name, category: f.category, body: f.body, language: f.language,
        complainant: person.name ? person : null,
      });
      setF(empty);
      onDone("Complaint queued. It becomes a case within a few seconds; refresh the list below.");
    } catch (err) {
      onDone(err instanceof Error ? err.message : "The complaint was not accepted.");
    }
  }

  return (
    <form className="filters" onSubmit={submit}>
      <label className="wide">Institution (as the complainant wrote it)<input value={f.institution_name} onChange={set("institution_name")} required minLength={3} maxLength={300} /></label>
      <label>Category<input value={f.category} onChange={set("category")} required minLength={3} maxLength={100} /></label>
      <label>Language
        <select value={f.language} onChange={set("language")}><option value="en">English</option><option value="hi">Hindi</option></select>
      </label>
      <label className="wide">Complaint<textarea value={f.body} onChange={set("body")} required minLength={20} maxLength={10000} rows={4} /></label>
      <label>Complainant name<input value={f.name} onChange={set("name")} maxLength={200} /></label>
      <label>E-mail<input type="email" value={f.email} onChange={set("email")} maxLength={254} /></label>
      <label>Phone<input value={f.phone} onChange={set("phone")} maxLength={20} /></label>
      <button type="submit">Queue complaint</button>
    </form>
  );
}

function UploadForm({ onDone }: { onDone: (message: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    try {
      const r = await upload<UploadResult>("/intake/upload", file);
      setResult(r);
      onDone(`${r.accepted} row(s) queued, ${r.rejected} refused.`);
    } catch (err) {
      setResult(null);
      onDone(err instanceof Error ? err.message : "The file was not accepted.");
    }
  }

  return (
    <>
      <form className="filters" onSubmit={send}>
        <label className="wide">
          CSV or XLSX file (columns: institution_name, category, body, and optionally language, filed_at,
          external_ref, complainant_name, complainant_email, complainant_phone)
          <input type="file" accept=".csv,.xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>
        <button type="submit" disabled={!file}>Upload</button>
      </form>
      {result && result.errors.length > 0 && (
        <p>
          {result.errors.length} problem(s) in {result.rejected} row(s).{" "}
          <button type="button" onClick={() => saveErrors(result.errors)}>Download error report</button>
        </p>
      )}
    </>
  );
}

function SourceLine({ s, isAdmin, onChanged }: { s: Source; isAdmin: boolean; onChanged: (m: string) => void }) {
  const [key, setKey] = useState<string | null>(null);

  async function change(body: object) {
    try {
      await api(`/intake/sources/${s.id}`, body, "PATCH");
      onChanged(`${s.name} saved. The change is recorded in the audit log.`);
    } catch (e) {
      onChanged(e instanceof Error ? e.message : "The change failed.");
    }
  }

  async function issue() {
    try {
      setKey((await api<{ api_key: string }>(`/intake/sources/${s.id}/key`, {})).api_key);
    } catch (e) {
      onChanged(e instanceof Error ? e.message : "No key was issued.");
    }
  }

  return (
    <tr>
      <th scope="row">{s.name}</th>
      <td>{s.channel}</td>
      <td>{s.bureau}</td>
      <td className="num">{s.priority}</td>
      <td>{s.fallback ?? "none"}</td>
      <td>
        {!s.active ? <strong className="flag">Inactive</strong> : s.marked_down ? <strong className="flag">Marked down</strong> : "Up"}
      </td>
      <td>{when(s.last_success_at)}</td>
      <td className="num">{s.failures > 0 ? <strong className="flag">{s.failures}</strong> : 0}</td>
      <td className="num">{s.pending}</td>
      <td className="num">{s.dead > 0 ? <strong className="flag">{s.dead}</strong> : 0}</td>
      {isAdmin && (
        <td>
          <button type="button" aria-label={`${s.marked_down ? "Mark up" : "Mark down"} ${s.name}`} onClick={() => change({ marked_down: !s.marked_down })}>
            {s.marked_down ? "Mark up" : "Mark down"}
          </button>{" "}
          <button type="button" aria-label={`${s.active ? "Deactivate" : "Activate"} ${s.name}`} onClick={() => change({ active: !s.active })}>{s.active ? "Deactivate" : "Activate"}</button>{" "}
          {s.channel === "api" && (
            <button type="button" aria-label={`${s.has_key ? "Replace" : "Issue"} API key for ${s.name}`} onClick={issue}>{s.has_key ? "Replace API key" : "Issue API key"}</button>
          )}
          {key && (
            <p role="status">
              New key (shown once, give it to the portal's operator now): <code style={{ wordBreak: "break-all" }}>{key}</code>
            </p>
          )}
        </td>
      )}
    </tr>
  );
}

function NewSource({ onChanged }: { onChanged: (m: string) => void }) {
  const empty = { name: "", channel: "api", bureau: "", priority: "1", fallback: "" };
  const [f, setF] = useState(empty);
  const set = (k: keyof typeof empty) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/intake/sources", { ...f, priority: Number(f.priority), fallback: f.fallback || null });
      setF(empty);
      onChanged(`${f.name} created. The change is recorded in the audit log.`);
    } catch (err) {
      onChanged(err instanceof Error ? err.message : "The source was not created.");
    }
  }

  return (
    <form className="filters" onSubmit={create}>
      <label>Name (lower case, digits, dashes)<input value={f.name} onChange={set("name")} pattern="[a-z0-9][a-z0-9-]{1,40}" required /></label>
      <label>Channel
        <select value={f.channel} onChange={set("channel")}>
          <option value="api">api</option><option value="spool">spool</option>
          <option value="upload">upload</option><option value="manual">manual</option>
        </select>
      </label>
      <label>Bureau code<input value={f.bureau} onChange={set("bureau")} required maxLength={10} /></label>
      <label>Priority<input type="number" min={1} max={9} value={f.priority} onChange={set("priority")} /></label>
      <label>Fallback source<input value={f.fallback} onChange={set("fallback")} /></label>
      <button type="submit">Create source</button>
    </form>
  );
}

function ItemTable({ items, onChanged, canReview }: { items: Item[]; onChanged: (m: string) => void; canReview: boolean }) {
  async function act(item: Item, what: "retry" | "reviewed") {
    try {
      await api(`/intake/items/${item.id}/${what}`, {});
      onChanged(what === "retry" ? "Put back in the queue. Recorded in the audit log." : "Marked reviewed. Recorded in the audit log.");
    } catch (e) {
      onChanged(e instanceof Error ? e.message : "The change failed.");
    }
  }

  if (items.length === 0) return <p className="note">Nothing here.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Received</th><th scope="col">Source</th><th scope="col">Path</th><th scope="col">Status</th>
          <th scope="col">Case</th><th scope="col" className="num">Attempts</th><th scope="col">Reason / next try</th>
          <th scope="col">Action</th>
        </tr>
      </thead>
      <tbody>
        {items.map((i) => (
          <tr key={i.id}>
            <td>{when(i.created_at)}</td>
            <td>{i.source} ({i.channel})</td>
            <td>{i.path}</td>
            <td>{i.status === "dead" ? <strong className="flag">Dead letter</strong> : i.status}</td>
            <td>
              {i.ref ?? (i.duplicate_of ? `duplicate of ${i.duplicate_of}` : "-")}
              {i.near_duplicate_of && <> (near duplicate of {i.near_duplicate_of}{i.review_state === "reviewed" ? ", reviewed" : ""})</>}
            </td>
            <td className="num">{i.attempts}</td>
            <td>{i.last_error ?? ""}{i.next_attempt_at && i.status === "pending" ? ` (next try ${when(i.next_attempt_at)})` : ""}</td>
            <td>
              {i.can_retry && <button type="button" aria-label={`Retry item from ${i.source} received ${when(i.created_at)}`} onClick={() => act(i, "retry")}>Retry</button>}
              {canReview && i.review_state === "pending" && (
                <button type="button" aria-label={`Mark ${i.ref} reviewed`} onClick={() => act(i, "reviewed")}>Mark reviewed</button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SourcesSection({ isAdmin, onChanged }: { isAdmin: boolean; onChanged: (m: string) => void }) {
  const sources = useLoad<Source[]>("/intake/sources");
  return (
    <>
      <h2>Sources</h2>
      {sources.error && <p role="alert">{sources.error}</p>}
      <table>
        <thead>
          <tr>
            <th scope="col">Source</th><th scope="col">Channel</th><th scope="col">Bureau</th>
            <th scope="col" className="num">Priority</th><th scope="col">Fallback</th><th scope="col">State</th>
            <th scope="col">Last success</th><th scope="col" className="num">Failures in a row</th>
            <th scope="col" className="num">Queued</th><th scope="col" className="num">Dead letters</th>
            {isAdmin && <th scope="col">Change</th>}
          </tr>
        </thead>
        <tbody>
          {(sources.data ?? []).map((s) => (
            <SourceLine key={`${s.id}${s.active}${s.marked_down}`} s={s} isAdmin={isAdmin} onChanged={onChanged} />
          ))}
        </tbody>
      </table>
      {isAdmin && <NewSource onChanged={onChanged} />}
    </>
  );
}

/** Intake: entering and uploading complaints (officers, bureau heads), source health (heads, oversight,
 * auditors, admin), dead letters with Retry and source set-up (admin). Rows show identifiers only. */
export function IntakePage({ role }: { role: string }) {
  const enters = ENTERS.includes(role);
  const isAdmin = role === "admin";
  const [message, setMessage] = useState<string | null>(null);
  const [show, setShow] = useState("");
  const [version, setVersion] = useState(0);
  const review = useLoad<Item[]>("/intake/items?review=true");
  const items = useLoad<Item[]>(`/intake/items${show ? `?status=${show}` : ""}`);

  function changed(text: string) {
    setMessage(text);
    setVersion((v) => v + 1);
    review.reload();
    items.reload();
  }

  return (
    <section>
      <h1>Intake</h1>
      <p className="note">
        Every complaint, from a portal's API, an uploaded file, this form or the spool folder, is queued first and then
        filed as a case. Failures are retried; nothing is dropped. No step leaves this deployment.
      </p>
      {message && <p role="status">{message}</p>}

      {enters && (
        <>
          <h2>Enter a complaint</h2>
          <ManualForm onDone={changed} />
          <h2>Upload a file</h2>
          <UploadForm onDone={changed} />
        </>
      )}

      {SEES_HEALTH.includes(role) && <SourcesSection key={version} isAdmin={isAdmin} onChanged={changed} />}

      {enters && (
        <>
          <h2>Near duplicates to review</h2>
          <ItemTable items={review.data ?? []} onChanged={changed} canReview />
        </>
      )}

      <h2>Queue</h2>
      <label>
        Show{" "}
        <select value={show} onChange={(e) => setShow(e.target.value)}>
          <option value="">All</option>
          <option value="pending">Waiting</option>
          <option value="dead">Dead letters</option>
          <option value="duplicate">Duplicates</option>
          <option value="done">Filed</option>
        </select>
      </label>{" "}
      <button type="button" onClick={() => changed("")}>Refresh</button>
      {items.error && <p role="alert">{items.error}</p>}
      <ItemTable items={items.data ?? []} onChanged={changed} canReview={enters} />
    </section>
  );
}
