import { useLoad } from "../../api";
import { InstitutionTimeline } from "../cases/History";
import { Links, SameInstitution } from "../overlaps/Overlaps";
import { type Profile, day, daysSince, place } from "./types";

export function InstitutionProfile({ id }: { id: string }) {
  const { data: p, error } = useLoad<Profile>(`/institutions/${id}`);
  if (error) return <p role="alert">{error}</p>;
  if (!p) return <p>Loading…</p>;
  const now = Date.now();

  return (
    <section>
      <p>
        <a href="#/institutions">← All institutions</a>
      </p>
      <h1>{p.name}</h1>
      <p>
        {place(p)}
        {p.permanent_id && <> · Permanent ID {p.permanent_id}</>}
      </p>
      {p.aliases.length > 0 && <p>Also written as: {p.aliases.map((a) => a.alias).join(" · ")}</p>}

      <dl className="tiles">
        <div>
          <dt>Bureaus involved</dt>
          <dd>{p.bureaus.join(", ") || "None"}</dd>
        </div>
        <div>
          <dt>Open cases</dt>
          <dd>{p.open}</dd>
        </div>
        <div>
          <dt>Closed cases</dt>
          <dd>{p.closed}</dd>
        </div>
        <div>
          <dt>Oldest open case</dt>
          <dd>{p.oldest_open ? `${p.oldest_open.ref}, ${daysSince(p.oldest_open.filed_at)} days` : "None"}</dd>
        </div>
      </dl>

      <SameInstitution institutionId={p.id} />
      <Links institutionId={p.id} />

      <h2>Cases from every bureau</h2>
      {p.complaints.length === 0 ? (
        <p>No cases are linked to this institution.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Bureau</th>
              <th>Category</th>
              <th>Status</th>
              <th>Filed</th>
              <th>Due</th>
            </tr>
          </thead>
          <tbody>
            {p.complaints.map((c) => (
              <tr key={c.id}>
                <td>
                  <a href={`#/cases/${c.id}`}>{c.ref}</a>
                </td>
                <td>{c.bureau}</td>
                <td>{c.category ?? "–"}</td>
                <td>{c.status.replace("_", " ")}</td>
                <td>{day(c.filed_at)}</td>
                <td>
                  {c.due_at ? day(c.due_at) : "–"}
                  {c.due_at && c.status !== "closed" && new Date(c.due_at).getTime() < now && (
                    <strong className="flag"> Overdue</strong>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="note">
        Complaint text stays with the bureau that holds the case.{" "}
        <a href={`#/cases?institution_id=${p.id}`}>Filter these cases</a>
      </p>

      <h2>History across these cases</h2>
      <InstitutionTimeline institutionId={p.id} />
    </section>
  );
}
