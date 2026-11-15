import { useState } from "react";
import { api, useLoad } from "../../api";
import { type Candidate, type QueueItem, day, place } from "./types";

export function ResolutionQueue({ canResolve }: { canResolve: boolean }) {
  const { data, error, reload } = useLoad<QueueItem[]>("/institutions/resolution/queue?limit=200");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function act(work: () => Promise<string>) {
    setBusy(true);
    try {
      setMessage(await work());
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    } finally {
      setBusy(false);
      reload();
    }
  }

  const run = () =>
    act(async () => {
      const r = await api<{ resolved: number; queued: number }>("/institutions/resolution/run", {});
      return `${r.resolved} linked automatically. ${r.queued} need a person.`;
    });

  const link = (item: QueueItem, c: Candidate) =>
    act(async () => {
      await api(`/institutions/resolution/${item.id}`, { institution_id: c.id });
      return `${item.ref} linked to ${c.name}. “${item.institution_name_raw}” will be recognised next time.`;
    });

  return (
    <section>
      <h1>Names that need a person</h1>
      <p>
        Cases whose institution could not be matched with confidence. Pick the right institution; the choice is
        recorded in the audit log.
      </p>
      {canResolve && (
        <button type="button" onClick={run} disabled={busy}>
          Run automatic matching
        </button>
      )}
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
      {data && data.length === 0 && <p>Nothing is waiting. Every case is linked to an institution.</p>}
      {data && data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Bureau</th>
              <th>Name as typed</th>
              <th>Best matches</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.ref}
                  <br />
                  <small>{day(item.filed_at)}</small>
                </td>
                <td>{item.bureau}</td>
                <td>{item.institution_name_raw}</td>
                <td>
                  {item.candidates.length === 0 && "No close match. Check the institution list."}
                  <ul className="candidates">
                    {item.candidates.map((c) => (
                      <li key={c.id}>
                        {canResolve && (
                          <button
                            type="button"
                            onClick={() => link(item, c)}
                            disabled={busy}
                            aria-label={`Link ${item.ref} to ${c.name}, ${place(c)}`}
                          >
                            Link
                          </button>
                        )}{" "}
                        <a href={`#/institutions/${c.id}`}>{c.name}</a>, {place(c)}{" "}
                        <small>
                          {c.score}% · {c.reason}
                        </small>
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
