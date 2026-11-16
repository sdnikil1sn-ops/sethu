import { useEffect } from "react";
import { useLoad } from "../../api";

// Mirrors backend/app/modules/dashboard/schemas.py
type Count = { key: string; label: string; total: number; open: number; overdue: number };
type OverdueCase = {
  id: string;
  ref: string;
  bureau: string;
  institution: string | null;
  category: string;
  status: string;
  due_at: string;
};
type Overview = {
  generated_at: string;
  totals: { total: number; open: number; overdue: number };
  by_bureau: Count[];
  by_status: Count[];
  by_category: Count[];
  weekly: { week: string; filed: number }[];
  attention: {
    overlaps_to_review: number;
    overlaps_confirmed: number;
    alerts_to_approve: number;
    alerts_unsent: number;
    findings_open: number;
    overdue_total: number;
    overdue: OverdueCase[];
  };
};

const REFRESH_MS = 30_000;
const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
const cases = (filter: string, value: string) => `#/cases?${new URLSearchParams({ [filter]: value })}`;

function CountTable({ title, filter, rows }: { title: string; filter: string; rows: Count[] }) {
  return (
    <table>
      <caption>
        <h2>{title}</h2>
      </caption>
      <thead>
        <tr>
          <th scope="col">{title.replace(/^By /, "")}</th>
          <th scope="col" className="num">All</th>
          <th scope="col" className="num">Open</th>
          <th scope="col" className="num">Overdue</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.key}>
            <th scope="row">
              <a href={cases(filter, r.key)}>{r.label.replace(/_/g, " ")}</a>
            </th>
            <td className="num">{r.total}</td>
            <td className="num">{r.open}</td>
            <td className="num">{r.overdue > 0 ? <strong className="flag">{r.overdue}</strong> : 0}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** Weekly filings as columns; the same numbers are in the table under it for screen readers and exact values. */
function Trend({ weeks }: { weeks: Overview["weekly"] }) {
  const max = Math.max(1, ...weeks.map((w) => w.filed));
  const width = 100 / weeks.length;
  return (
    <figure className="trend">
      <svg viewBox="0 0 100 40" preserveAspectRatio="none" role="img" aria-label="Complaints filed per week">
        {weeks.map((w, i) => (
          <rect key={w.week} x={i * width + width * 0.15} width={width * 0.7} y={40 - (w.filed / max) * 38}
                height={(w.filed / max) * 38}>
            <title>{`Week of ${day(w.week)}: ${w.filed}`}</title>
          </rect>
        ))}
      </svg>
      <figcaption>
        Week of {day(weeks[0].week)} to week of {day(weeks[weeks.length - 1].week)}; highest week {max}.
      </figcaption>
      <details>
        <summary>Show the numbers</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Week of</th>
              <th scope="col" className="num">Filed</th>
            </tr>
          </thead>
          <tbody>
            {weeks.map((w) => (
              <tr key={w.week}>
                <td>{day(w.week)}</td>
                <td className="num">{w.filed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}

/** Counts across every bureau (reference, status and category only, never complaint text) and what needs a person. */
export function Dashboard() {
  const { data, error, reload } = useLoad<Overview>("/dashboard");
  useEffect(() => {
    const timer = window.setInterval(reload, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [reload]);

  if (!data) return error ? <p role="alert">{error}</p> : <p>Loading…</p>;
  const a = data.attention;
  return (
    <section>
      <h1>Dashboard</h1>
      <p className="note">
        Updated {new Date(data.generated_at).toLocaleTimeString("en-IN")}; refreshes every 30 seconds.{" "}
        <button type="button" onClick={reload}>
          Refresh now
        </button>
      </p>
      {error && <p role="alert">Could not refresh: {error}</p>}

      <h2>Needs attention</h2>
      <ul>
        <li>
          <a href="#/overlaps">
            {a.overlaps_to_review} overlap suggestion{a.overlaps_to_review === 1 ? "" : "s"} awaiting review
          </a>{" "}
          <small>({a.overlaps_confirmed} confirmed)</small>
        </li>
        <li>
          <a href="#/alerts">
            {a.alerts_to_approve} alert{a.alerts_to_approve === 1 ? "" : "s"} awaiting approval
          </a>
          {a.alerts_unsent > 0 && (
            <>
              {" "}
              <small>({a.alerts_unsent} approved but not sent yet)</small>
            </>
          )}
        </li>
        <li>
          <a href="#/findings">
            {a.findings_open} open finding{a.findings_open === 1 ? "" : "s"}
          </a>{" "}
          <small>(transfer loops, stalled transfers, bottlenecks)</small>
        </li>
        <li>
          <a href={cases("overdue", "true")}>{a.overdue_total} overdue case{a.overdue_total === 1 ? "" : "s"}</a>
          {a.overdue.length < a.overdue_total && <small> (the {a.overdue.length} most overdue below)</small>}
        </li>
      </ul>
      {a.overdue.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Case</th>
              <th scope="col">Bureau</th>
              <th scope="col">Institution</th>
              <th scope="col">Category</th>
              <th scope="col">Status</th>
              <th scope="col">Was due</th>
            </tr>
          </thead>
          <tbody>
            {a.overdue.map((c) => (
              <tr key={c.id}>
                <td>
                  <a href={`#/cases/${c.id}`}>{c.ref}</a>
                </td>
                <td>{c.bureau}</td>
                <td>{c.institution ?? "Not matched yet"}</td>
                <td>{c.category}</td>
                <td>{c.status.replace(/_/g, " ")}</td>
                <td className="flag">{day(c.due_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <dl className="tiles">
        <div>
          <dt>All cases</dt>
          <dd>{data.totals.total}</dd>
        </div>
        <div>
          <dt>Open</dt>
          <dd>{data.totals.open}</dd>
        </div>
        <div>
          <dt>Overdue</dt>
          <dd className={data.totals.overdue ? "flag" : undefined}>{data.totals.overdue}</dd>
        </div>
      </dl>

      <h2>Complaints filed per week</h2>
      <Trend weeks={data.weekly} />
      <CountTable title="By bureau" filter="bureau" rows={data.by_bureau} />
      <CountTable title="By status" filter="status" rows={data.by_status} />
      <CountTable title="By category" filter="category" rows={data.by_category} />
    </section>
  );
}
