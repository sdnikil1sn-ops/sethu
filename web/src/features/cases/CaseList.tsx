import { useEffect, useState } from "react";
import { useLoad } from "../../api";
import { type CasePage, type Options, day, sla, words } from "./types";

const PAGE = 50;
const EMPTY = {
  q: "",
  bureau: "",
  category: "",
  status: "",
  institution_id: "",
  state: "",
  filed_from: "",
  filed_to: "",
  overdue: "",
  overlapping: "",
};
type Filters = typeof EMPTY;

/** `initial` is the query part of the URL hash, e.g. "institution_id=…" from an institution page. */
export function CaseList({ initial }: { initial: string }) {
  const [filters, setFilters] = useState<Filters>({ ...EMPTY, ...Object.fromEntries(new URLSearchParams(initial)) });
  const [q, setQ] = useState(filters.q);
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setQ(filters.q.trim()), 250); // do not query on every key press
    return () => clearTimeout(timer);
  }, [filters.q]);

  const set = (name: keyof Filters) => (e: { target: { value: string } }) => {
    setFilters((f) => ({ ...f, [name]: e.target.value }));
    setOffset(0);
  };

  const query = new URLSearchParams({ limit: String(PAGE), offset: String(offset) });
  const shared = new URLSearchParams();
  for (const [name, value] of Object.entries({ ...filters, q })) if (value) (query.set(name, value), shared.set(name, value));

  // Keep the filters in the address so a filtered view can be bookmarked or shared. replaceState does not
  // fire hashchange, so the list is not rebuilt (and the search box keeps focus) while someone types.
  const sharedQuery = shared.toString();
  useEffect(() => {
    const hash = `#/cases${sharedQuery ? `?${sharedQuery}` : ""}`;
    if (window.location.hash !== hash) window.history.replaceState(null, "", hash);
  }, [sharedQuery]);

  const { data: options } = useLoad<Options>("/cases/options");
  const { data: institutions } = useLoad<{ id: string; name: string }[]>("/institutions?limit=200");
  const { data, error } = useLoad<CasePage>(`/cases?${query}`);

  const choose = (label: string, name: keyof Filters, choices: [string, string][]) => (
    <label>
      {label}
      <select value={filters[name]} onChange={set(name)}>
        <option value="">All</option>
        {choices.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <section>
      <h1>Cases</h1>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label className="wide">
          Search reference, institution or complaint text
          <input type="search" value={filters.q} onChange={set("q")} placeholder="e.g. C-101 or refund" />
        </label>
        {choose("Unit", "bureau", (options?.bureaus ?? []).map((b) => [b.code, `${b.code}: ${b.name}`]))}
        {choose("Category", "category", (options?.categories ?? []).map((c) => [c, c]))}
        {choose("Status", "status", (options?.statuses ?? []).map((s) => [s, words(s)]))}
        {choose("Institution", "institution_id", (institutions ?? []).map((i) => [i.id, i.name]))}
        {choose("State", "state", (options?.states ?? []).map((s) => [s, s]))}
        <label>
          Filed from
          <input type="date" value={filters.filed_from} onChange={set("filed_from")} />
        </label>
        <label>
          Filed to
          <input type="date" value={filters.filed_to} onChange={set("filed_to")} />
        </label>
        {choose("Overdue", "overdue", [
          ["true", "Overdue only"],
          ["false", "Not overdue"],
        ])}
        {choose("Overlaps", "overlapping", [["true", "Overlapping only"]])}
        <button
          type="button"
          onClick={() => {
            setFilters(EMPTY);
            setOffset(0);
          }}
        >
          Clear filters
        </button>
      </form>
      <p className="note">
        Complaint text is searched only in cases you are allowed to read. The address of this page keeps the
        filters, so you can bookmark or share this view.
      </p>

      {error && <p role="alert">{error}</p>}
      {data && (
        <p role="status">
          {data.total === 0
            ? "No case matches these filters."
            : `${data.total} case${data.total === 1 ? "" : "s"}. Showing ${offset + 1} to ${offset + data.items.length}.`}
        </p>
      )}
      {data && data.items.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Unit</th>
                <th>Institution</th>
                <th>Category</th>
                <th>Status</th>
                <th>Filed</th>
                <th>21-day clock</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
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
                    {c.institution ?? "Not matched yet"}
                    {c.state && (
                      <>
                        <br />
                        <small>{c.state}</small>
                      </>
                    )}
                  </td>
                  <td>{c.category ?? "–"}</td>
                  <td>{words(c.status)}</td>
                  <td>{day(c.filed_at)}</td>
                  <td>{c.overdue ? <strong className="flag">{sla(c)}</strong> : sla(c)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
              Previous
            </button>{" "}
            <button type="button" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>
              Next
            </button>
          </p>
        </>
      )}
    </section>
  );
}
