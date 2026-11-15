import { useEffect, useState } from "react";
import { useLoad } from "../../api";
import { type InstitutionRow, place } from "./types";

export function InstitutionList() {
  const [typed, setTyped] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => setQ(typed.trim()), 250); // do not query on every key press
    return () => clearTimeout(timer);
  }, [typed]);

  const { data, error } = useLoad<InstitutionRow[]>(`/institutions?${new URLSearchParams(q ? { q } : { limit: "200" })}`);

  return (
    <section>
      <h1>Institutions</h1>
      <label>
        Search by name, alias or acronym
        <input
          type="search"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          placeholder="e.g. GIT Pune"
          autoFocus
        />
      </label>
      {error && <p role="alert">{error}</p>}
      {data && data.length === 0 && <p>No institution matches “{q}”.</p>}
      {data && data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Institution</th>
              <th>Place</th>
              {q ? <th>Matched spelling</th> : <th className="num">Cases</th>}
              {q ? <th className="num">Match</th> : <th className="num">Open</th>}
            </tr>
          </thead>
          <tbody>
            {data.map((i) => (
              <tr key={i.id}>
                <td>
                  <a href={`#/institutions/${i.id}`}>{i.name}</a>
                </td>
                <td>{place(i)}</td>
                {q ? <td>{i.matched ?? "–"}</td> : <td className="num">{i.complaints}</td>}
                {q ? <td className="num">{i.score}%</td> : <td className="num">{i.open}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
