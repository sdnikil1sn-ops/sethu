import { useEffect, useState } from "react";
import { useLoad } from "../../api";
import { type InstitutionRow, place } from "./types";

/** Uses the same institution search as the top-bar search box (GET /institutions?q= calls it). */
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
        Search by name, other spelling, initials, city, state or permanent id
        <input
          type="search"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          placeholder="e.g. Greenfield, GIT, Madurai, Tamil Nadu"
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
              <th className="num">Cases</th>
              <th className="num">Open</th>
              {q && <th>Matched on</th>}
            </tr>
          </thead>
          <tbody>
            {data.map((i) => (
              <tr key={i.id}>
                <td>
                  <a href={`#/institutions/${i.id}`}>{i.name}</a>
                </td>
                <td>{place(i)}</td>
                <td className="num">{i.complaints}</td>
                <td className="num">{i.open}</td>
                {q && <td>{i.why ?? "–"}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
