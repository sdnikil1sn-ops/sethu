import { useEffect, useState } from "react";
import { useLoad } from "../../api";
import { Pager, pageFrom } from "../../Pager";
import { type CasePage, type Options, day, sla, words } from "./types";

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
  const [filters, setFilters] = useState<Filters>(() => {
    const given = Object.fromEntries(new URLSearchParams(initial));
    return { ...EMPTY, ...Object.fromEntries(Object.entries(given).filter(([k]) => k in EMPTY)) };
  });
  const [q, setQ] = useState(filters.q);
  const [{ limit, offset }, setPage] = useState(() => pageFrom(new URLSearchParams(initial)));
  const setOffset = (o: number) => setPage((p) => ({ ...p, offset: o }));
  useEffect(() => {
    const timer = setTimeout(() => setQ(filters.q.trim()), 250); // do not query on every key press
    return () => clearTimeout(timer);
  }, [filters.q]);

  const set = (name: keyof Filters) => (e: { target: { value: string } }) => {
    setFilters((f) => ({ ...f, [name]: e.target.value }));
    setOffset(0);
  };

  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const shared = new URLSearchParams();
  for (const [name, value] of Object.entries({ ...filters, q })) if (value) (query.set(name, value), shared.set(name, value));
  if (limit !== 50) shared.set("limit", String(limit));
  if (offset) shared.set("offset", String(offset));

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
      {data && <Pager page={data} noun="cases" onChange={(l, o) => setPage({ limit: l, offset: o })} />}
      {data && data.items.length > 0 && (
        <>
          <table className="stack" role="table">
            <thead role="rowgroup">
              <tr role="row">
                <th role="columnheader">Case</th>
                <th role="columnheader">Unit</th>
                <th role="columnheader">Institution</th>
                <th role="columnheader">Category</th>
                <th role="columnheader">Status</th>
                <th role="columnheader">Filed</th>
                <th role="columnheader">21-day clock</th>
              </tr>
            </thead>
            <tbody role="rowgroup">
              {data.items.map((c) => (
                <tr role="row" key={c.id}>
                  <td role="cell" data-label="Case">
                    <a href={`#/cases/${c.id}`}>{c.ref}</a>
                    {!c.readable && (
                      <>
                        <br />
                        <small>summary only</small>
                      </>
                    )}
                  </td>
                  <td role="cell" data-label="Unit">{c.bureau}</td>
                  <td role="cell" data-label="Institution">
                    {c.institution ?? "Not matched yet"}
                    {c.state && (
                      <>
                        <br />
                        <small>{c.state}</small>
                      </>
                    )}
                  </td>
                  <td role="cell" data-label="Category">{c.category ?? "–"}</td>
                  <td role="cell" data-label="Status">{words(c.status)}</td>
                  <td role="cell" data-label="Filed">{day(c.filed_at)}</td>
                  <td role="cell" data-label="21-day clock">{c.overdue ? <strong className="flag">{sla(c)}</strong> : sla(c)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
