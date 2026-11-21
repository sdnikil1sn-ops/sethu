import { useLoad } from "../../api";
import { type CaseRow, day, sla, words } from "./types";

type WorkloadRow = { bureau: string; assignee_id: string | null; assignee: string | null; role: string | null; open: number; overdue: number };

/** An officer's queue: open cases assigned to them, soonest deadline first. */
export function MyCases() {
  const { data, error } = useLoad<CaseRow[]>("/cases/mine");
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading…</p>;
  return (
    <section>
      <h1>My cases</h1>
      <p className="note">Open cases assigned to you, soonest deadline first. Anyone in your bureau can assign or reassign a case from its page.</p>
      {data.length === 0 ? (
        <p>No open cases are assigned to you.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Case</th><th scope="col">Institution</th><th scope="col">Category</th>
              <th scope="col">Status</th><th scope="col">Due</th><th scope="col">Clock</th>
            </tr>
          </thead>
          <tbody>
            {data.map((c) => (
              <tr key={c.id}>
                <th scope="row"><a href={`#/cases/${c.id}`}>{c.ref}</a></th>
                <td>{c.institution ?? "not matched yet"}</td>
                <td>{c.category ?? "–"}</td>
                <td>{words(c.status)}</td>
                <td>{c.due_at ? day(c.due_at) : "–"}</td>
                <td className={c.overdue ? "flag" : undefined}>{sla(c)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

/** A bureau head's view of who holds what: open and overdue cases per person, and the unassigned ones. */
export function Workload() {
  const { data, error } = useLoad<WorkloadRow[]>("/cases/workload");
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading…</p>;
  const bureaus = [...new Set(data.map((r) => r.bureau))];
  return (
    <section>
      <h1>Workload</h1>
      <p className="note">
        Open cases (not closed, not waiting for a transfer to be acknowledged) per person. Assign a case from its page.
      </p>
      {bureaus.map((b) => (
        <table key={b}>
          <caption>{b}</caption>
          <thead>
            <tr>
              <th scope="col">Person</th><th scope="col" className="num">Open</th><th scope="col" className="num">Overdue</th>
            </tr>
          </thead>
          <tbody>
            {data
              .filter((r) => r.bureau === b)
              .map((r) => (
                <tr key={r.assignee_id ?? "unassigned"}>
                  <th scope="row">
                    {r.assignee_id ? `${r.assignee} (${words(r.role ?? "")})` : <strong className="flag">Unassigned</strong>}
                  </th>
                  <td className="num">{r.open}</td>
                  <td className="num">{r.overdue > 0 ? <strong className="flag">{r.overdue}</strong> : 0}</td>
                </tr>
              ))}
          </tbody>
        </table>
      ))}
    </section>
  );
}
