import { useState } from "react";
import { useLoad } from "../../api";
import { day, words } from "../cases/types";

// Mirrors backend/app/modules/search/schemas.py
type InstitutionHit = {
  id: string;
  permanent_id: string | null;
  name: string;
  state: string | null;
  district: string | null;
  score: number;
  why: string;
};
type ComplaintHit = {
  id: string;
  ref: string;
  bureau: string;
  institution_id: string | null;
  institution: string | null;
  category: string;
  status: string;
  filed_at: string;
  readable: boolean;
  why: string[];
};
type Results = { q: string; institutions: InstitutionHit[]; complaints: { total: number; items: ComplaintHit[] } };

/** The search box in the top bar. Submitting opens the results screen. */
export function SearchBox({ initial }: { initial: string }) {
  const [q, setQ] = useState(initial);
  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        if (q.trim().length >= 2) window.location.hash = `#/search?${new URLSearchParams({ q: q.trim() })}`;
      }}
    >
      <input
        type="search"
        aria-label="Search institutions and cases"
        placeholder="Search: GIT Pune, C-101, Fee refund…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        minLength={2}
        maxLength={200}
      />{" "}
      <button type="submit">Search</button>
    </form>
  );
}

/** Results grouped as institutions and cases, each with why it matched. */
export function SearchResults({ q }: { q: string }) {
  const { data, error } = useLoad<Results>(`/search?${new URLSearchParams({ q, limit: "50" })}`);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Searching…</p>;
  const cases = data.complaints;

  return (
    <section>
      <h1>Search: “{data.q}”</h1>
      <p className="note">
        Institutions are matched by name, other spellings, initials, city, state and permanent id (the same search as
        the Institutions screen); cases by reference, category, status,
        bureau and institution. Complaint text is searched only in cases you are allowed to read.
      </p>

      <h2>Institutions ({data.institutions.length})</h2>
      {data.institutions.length === 0 ? (
        <p>No institution matches.</p>
      ) : (
        <ul className="hits">
          {data.institutions.map((i) => (
            <li key={i.id}>
              <a href={`#/institutions/${i.id}`}>{i.name}</a>{" "}
              <small>
                {[i.district, i.state].filter(Boolean).join(", ")} · matched on {i.why}
              </small>
            </li>
          ))}
        </ul>
      )}

      <h2>Cases ({cases.total})</h2>
      {cases.items.length === 0 ? (
        <p>No case matches.</p>
      ) : (
        <>
          {cases.total > cases.items.length && (
            <p className="note">
              Showing the first {cases.items.length}. <a href={`#/cases?${new URLSearchParams({ q })}`}>Open all in the case list</a>
              , where you can filter further.
            </p>
          )}
          <table>
            <thead>
              <tr>
                <th scope="col">Case</th>
                <th scope="col">Bureau</th>
                <th scope="col">Institution</th>
                <th scope="col">Category</th>
                <th scope="col">Status</th>
                <th scope="col">Filed</th>
                <th scope="col">Matched on</th>
              </tr>
            </thead>
            <tbody>
              {cases.items.map((c) => (
                <tr key={c.id}>
                  <td>
                    <a href={`#/cases/${c.id}`}>{c.ref}</a>
                    {!c.readable && (
                      <>
                        <br />
                        <small>summary only</small>
                      </>
                    )}
                  </td>
                  <td>{c.bureau}</td>
                  <td>
                    {c.institution_id ? (
                      <a href={`#/institutions/${c.institution_id}`}>{c.institution}</a>
                    ) : (
                      "Not matched yet"
                    )}
                  </td>
                  <td>{c.category}</td>
                  <td>{words(c.status)}</td>
                  <td>{day(c.filed_at)}</td>
                  <td>{c.why.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
