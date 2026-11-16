import { type FormEvent, useState } from "react";
import { api, useLoad } from "../../api";
import { History } from "./History";
import { type Case, type Options, day, sla, words } from "./types";

// Mirrors ACTIONS in backend/app/modules/complaints/service.py: what each status allows.
const ACTIONS: { id: string; label: string; from: string[] }[] = [
  { id: "acknowledge", label: "Acknowledge transfer", from: ["transferred"] },
  { id: "assign", label: "Assign", from: ["open", "in_progress", "replied"] },
  { id: "note", label: "Add note", from: ["open", "in_progress", "replied", "transferred"] },
  { id: "reply", label: "Reply received", from: ["open", "in_progress"] },
  { id: "transfer", label: "Transfer to another unit", from: ["open", "in_progress", "replied", "transferred"] },
  { id: "close", label: "Close", from: ["open", "in_progress", "replied"] },
];

function ActionForm({ c, onDone }: { c: Case; onDone: (updated: Case) => void }) {
  const allowed = ACTIONS.filter((a) => a.from.includes(c.status));
  const [action, setAction] = useState(allowed[0]?.id ?? "");
  const [note, setNote] = useState("");
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { data: options } = useLoad<Options>("/cases/options");
  const { data: staff } = useLoad<{ id: string; display_name: string; role: string }[]>(`/cases/${c.id}/assignees`);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body = {
        action,
        note: note || null,
        to_bureau: action === "transfer" ? target : null,
        assignee_id: action === "assign" ? target : null,
      };
      onDone(await api<Case>(`/cases/${c.id}/actions`, body));
    } catch (err) {
      setError(err instanceof Error ? err.message : "The request failed.");
      setBusy(false);
    }
  }

  const others = (options?.bureaus ?? []).filter((b) => b.code !== c.bureau);
  return (
    <form className="action" onSubmit={submit}>
      <h2>Take action</h2>
      <label>
        Action
        <select
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setTarget("");
          }}
        >
          {allowed.map((a) => (
            <option key={a.id} value={a.id}>
              {a.label}
            </option>
          ))}
        </select>
      </label>
      {action === "assign" && (
        <label>
          Assign to
          <select value={target} onChange={(e) => setTarget(e.target.value)} required>
            <option value="">Choose a person</option>
            {(staff ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.display_name} ({words(s.role)})
              </option>
            ))}
          </select>
        </label>
      )}
      {action === "transfer" && (
        <label>
          Transfer to
          <select value={target} onChange={(e) => setTarget(e.target.value)} required>
            <option value="">Choose a unit</option>
            {others.map((b) => (
              <option key={b.code} value={b.code}>
                {b.code}: {b.name}
              </option>
            ))}
          </select>
        </label>
      )}
      <label>
        Note{action === "note" ? "" : " (optional)"}
        <textarea value={note} onChange={(e) => setNote(e.target.value)} required={action === "note"} maxLength={2000} />
      </label>
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={busy}>
        Record action
      </button>
      <p className="note">Recorded in the case history and the audit log. It cannot be edited afterwards.</p>
    </form>
  );
}

export function CaseDetail({ id }: { id: string }) {
  const { data, error } = useLoad<Case>(`/cases/${id}`);
  const [updated, setUpdated] = useState<Case | null>(null);
  if (error) return <p role="alert">{error}</p>;
  const c = updated ?? data;
  if (!c) return <p>Loading…</p>;

  return (
    <section>
      <p>
        <a href="#/cases">← All cases</a>
      </p>
      <h1>
        {c.ref} <small>{words(c.status)}</small>
      </h1>
      {c.awaiting_acknowledgement && (
        <p role="status">Transferred to {c.bureau}. Waiting for {c.bureau} to acknowledge.</p>
      )}

      <dl className="tiles">
        <div>
          <dt>Unit holding the case</dt>
          <dd>{c.bureau}</dd>
        </div>
        <div>
          <dt>Filed</dt>
          <dd>{day(c.filed_at)}</dd>
        </div>
        <div>
          <dt>Due (21 days)</dt>
          <dd>{c.due_at ? day(c.due_at) : "–"}</dd>
        </div>
        <div>
          <dt>Clock</dt>
          <dd className={c.overdue ? "flag" : undefined}>{sla(c)}</dd>
        </div>
      </dl>
      <p>
        Institution:{" "}
        {c.institution_id ? <a href={`#/institutions/${c.institution_id}`}>{c.institution}</a> : "not matched yet"}
        {c.institution_name_raw && c.institution_name_raw !== c.institution && <> (typed as “{c.institution_name_raw}”)</>}
        {c.category && <> · Category: {c.category}</>}
      </p>

      <h2>Complaint</h2>
      {c.readable ? (
        <p className="complaint" lang={c.language ?? undefined}>
          {c.body}
        </p>
      ) : (
        <p role="note">
          This case is held by {c.bureau_name} ({c.bureau}). The complaint text and history are visible to that unit
          only. Contact its head to coordinate.
        </p>
      )}

      {c.readable && (
        <>
          <h2>History</h2>
          <History actions={c.history} />
        </>
      )}
      {/* key: a fresh form, with the actions the new status allows, after each recorded action */}
      {c.can_act && <ActionForm key={c.history.length} c={c} onDone={setUpdated} />}
    </section>
  );
}
