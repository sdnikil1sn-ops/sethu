// Paging for the long lists (cases, findings, overlaps). Mirrors backend/app/db/paging.py.
export type PageMeta = { total: number; total_capped: boolean; has_next: boolean; limit: number; offset: number };
export type Page<T> = PageMeta & { items: T[] };

export const PAGE_SIZES = [25, 50, 100, 200];
export const COUNT_CAP = 1000;

/** A count that may be capped: more than COUNT_CAP reads "1,000+". */
export const count = (n: number, capped = n > COUNT_CAP) =>
  capped ? `${COUNT_CAP.toLocaleString("en-IN")}+` : n.toLocaleString("en-IN");

/** "limit" and "offset" from the address's query part, with the defaults the API uses. */
export function pageFrom(params: URLSearchParams): { limit: number; offset: number } {
  const limit = Number(params.get("limit"));
  const offset = Number(params.get("offset"));
  return {
    limit: PAGE_SIZES.includes(limit) ? limit : 50,
    offset: Number.isInteger(offset) && offset > 0 ? offset : 0,
  };
}

export function Pager({
  page,
  noun,
  onChange,
}: {
  page: PageMeta & { items: unknown[] };
  noun: string;
  onChange: (limit: number, offset: number) => void;
}) {
  const { limit, offset, items } = page;
  const first = offset + 1;
  const last = offset + items.length;
  const number = Math.floor(offset / limit) + 1;
  return (
    <nav className="pager" aria-label={`Pages of ${noun}`}>
      <p role="status">
        {items.length === 0
          ? offset > 0
            ? `No ${noun} on this page.`
            : `No ${noun} match.`
          : `Page ${number}: ${first.toLocaleString("en-IN")} to ${last.toLocaleString("en-IN")} of ${count(page.total, page.total_capped)} ${noun}.`}
      </p>
      <button type="button" disabled={offset === 0} onClick={() => onChange(limit, Math.max(0, offset - limit))}>
        Previous page
      </button>
      <button type="button" disabled={!page.has_next} onClick={() => onChange(limit, offset + limit)}>
        Next page
      </button>
      <label>
        Per page
        <select value={limit} onChange={(e) => onChange(Number(e.target.value), 0)}>
          {PAGE_SIZES.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>
    </nav>
  );
}
