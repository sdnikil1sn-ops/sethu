import { useState } from "react";
import { api, useLoad } from "../../api";
import { GlossaryAdmin } from "./Glossary";

// Mirrors backend/app/modules/bureaus/schemas.py and users/schemas.py
type BureauRow = {
  id: string;
  code: string;
  name: string;
  active: boolean;
  cases: number;
  people: number;
  heads_with_email: number;
};
type Person = {
  id: string;
  display_name: string;
  email: string | null;
  role: string;
  bureau: string | null;
  active: boolean;
  no_email: boolean;
};

function BureauLine({ b, onChanged }: { b: BureauRow; onChanged: (message: string) => void }) {
  const [name, setName] = useState(b.name);
  const [busy, setBusy] = useState(false);

  async function save(change: { name?: string; active?: boolean }) {
    setBusy(true);
    try {
      await api(`/admin/bureaus/${b.id}`, change, "PATCH");
      onChanged(`${b.code} saved. The change is recorded in the audit log.`);
    } catch (e) {
      onChanged(e instanceof Error ? e.message : "The change failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <tr>
      <th scope="row">{b.code}</th>
      <td>
        <input aria-label={`Name of ${b.code}`} value={name} onChange={(e) => setName(e.target.value)} />{" "}
        {name.trim() !== b.name && (
          <button type="button" disabled={busy || name.trim().length < 3} onClick={() => save({ name })} aria-label={`Save name of ${b.code}`}>
            Save name
          </button>
        )}
      </td>
      <td>{b.active ? "Active" : <strong className="flag">Deactivated</strong>}</td>
      <td className="num">{b.cases}</td>
      <td className="num">{b.people}</td>
      <td className="num">
        {b.heads_with_email === 0 ? <strong className="flag">0: alerts reach nobody</strong> : b.heads_with_email}
      </td>
      <td>
        <button type="button" disabled={busy} onClick={() => save({ active: !b.active })} aria-label={`${b.active ? "Deactivate" : "Reactivate"} ${b.code}`}>
          {b.active ? "Deactivate" : "Reactivate"}
        </button>
      </td>
    </tr>
  );
}

type Deadline = { category: string; days: number | null; effective_days: number; default_days: number };

/** Days to close a case, per category. Used for new and reopened cases; open cases keep their deadline. */
function Deadlines() {
  const { data, error, reload } = useLoad<Deadline[]>("/admin/deadlines");
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string | null>(null);

  async function save(category: string) {
    try {
      await api(`/admin/deadlines/${encodeURIComponent(category)}`, { days: Number(edits[category]) }, "PUT");
      setMessage(`${category}: ${edits[category]} days. Recorded in the audit log.`);
      setEdits({ ...edits, [category]: "" });
      reload();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The deadline was not saved.");
    }
  }

  return (
    <>
      <h2>Deadlines by category</h2>
      <p className="note">
        A category without its own setting uses the default ({data?.[0]?.default_days ?? "–"} days). A missed deadline
        becomes a finding and an alert, held for approval, to the head of the bureau holding the case.
      </p>
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
      <table>
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col" className="num">Days</th>
            <th scope="col">Change</th>
          </tr>
        </thead>
        <tbody>
          {(data ?? []).map((d) => (
            <tr key={d.category}>
              <th scope="row">{d.category}</th>
              <td className="num">{d.days ?? `${d.effective_days} (default)`}</td>
              <td>
                <input
                  type="number"
                  min={1}
                  max={365}
                  aria-label={`Days for ${d.category}`}
                  value={edits[d.category] ?? ""}
                  onChange={(e) => setEdits({ ...edits, [d.category]: e.target.value })}
                />{" "}
                <button type="button" disabled={!edits[d.category]} onClick={() => save(d.category)} aria-label={`Save days for ${d.category}`}>
                  Save
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/** Admin: bureaus (create, rename, deactivate; every change audited) and the people SETHU knows. */
export function AdminPage() {
  const bureaus = useLoad<BureauRow[]>("/admin/bureaus");
  const people = useLoad<Person[]>("/admin/users");
  const [draft, setDraft] = useState({ code: "", name: "" });
  const [message, setMessage] = useState<string | null>(null);

  function changed(text: string) {
    setMessage(text);
    bureaus.reload();
  }

  async function create(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api("/admin/bureaus", { code: draft.code.trim(), name: draft.name.trim() });
      setDraft({ code: "", name: "" });
      changed(`${draft.code.trim().toUpperCase()} created. The change is recorded in the audit log.`);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "The bureau was not created.");
    }
  }

  const missing = (people.data ?? []).filter((p) => p.no_email);
  return (
    <section>
      <h1>Admin</h1>
      <h2>Bureaus</h2>
      <p className="note">
        A bureau is deactivated, never deleted: its cases and history stay, and it can no longer receive transfers.
        The code cannot change once created.
      </p>
      {message && <p role="status">{message}</p>}
      {bureaus.error && <p role="alert">{bureaus.error}</p>}
      {bureaus.data && (
        <table>
          <thead>
            <tr>
              <th scope="col">Code</th>
              <th scope="col">Name</th>
              <th scope="col">Status</th>
              <th scope="col" className="num">Cases</th>
              <th scope="col" className="num">People</th>
              <th scope="col" className="num">Heads with e-mail</th>
              <th scope="col">Change</th>
            </tr>
          </thead>
          <tbody>
            {bureaus.data.map((b) => (
              <BureauLine key={`${b.id}${b.name}${b.active}`} b={b} onChanged={changed} />
            ))}
          </tbody>
        </table>
      )}
      <form className="filters" onSubmit={create}>
        <label>
          New bureau code
          <input value={draft.code} onChange={(e) => setDraft({ ...draft, code: e.target.value })} maxLength={20} />
        </label>
        <label className="wide">
          Name
          <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} maxLength={200} />
        </label>
        <button type="submit" disabled={draft.code.trim().length < 2 || draft.name.trim().length < 3}>
          Create bureau
        </button>
      </form>

      <Deadlines />
      <GlossaryAdmin />

      <h2>People</h2>
      <p className="note">
        People come from Keycloak and are brought up to date each time they sign in. Alert mail goes to the e-mail
        address stored here; set a missing one in Keycloak and the person's next sign-in brings it in.
      </p>
      {missing.length > 0 && (
        <p className="flag" role="status">
          {missing.length} {missing.length === 1 ? "person has" : "people have"} no e-mail address: alert mail cannot
          reach {missing.length === 1 ? "them" : "them"}.
        </p>
      )}
      {people.error && <p role="alert">{people.error}</p>}
      {people.data && (
        <table>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Role</th>
              <th scope="col">Bureau</th>
              <th scope="col">E-mail</th>
            </tr>
          </thead>
          <tbody>
            {people.data.map((p) => (
              <tr key={p.id}>
                <td>{p.display_name}</td>
                <td>{p.role.replace("_", " ")}</td>
                <td>{p.bureau ?? "–"}</td>
                <td>{p.no_email ? <strong className="flag">No e-mail</strong> : p.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
