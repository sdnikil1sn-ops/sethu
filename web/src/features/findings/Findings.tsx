import { useState } from "react";
import { api, useLoad } from "../../api";
import type { Options } from "../cases/types";

// Mirrors backend/app/modules/findings/schemas.py
export type Finding = {
  id: string;
  kind: "transfer_loop" | "stalled_transfer" | "bottleneck";
  status: "open" | "resolved" | "dismissed";
  first_seen: string;
  decided_at: string | null;
  decided_by: string | null;
  evidence: Record<string, number | string | string[] | null>;
  complaint_id: string | null;
  ref: string | null;
  institution_id: string | null;
  institution: string | null;
  bureaus: string[];
  alert_id: string | null;
  alert_status: string | null;
};
type Trend = {
  days: number;
  items: { institution_id: string; institution: string; state: string | null; recent: number; previous: number; bureaus: string[] }[];
};

const KIND = {
  transfer_loop: "Bottleneck detected: transfer loop",
  stalled_transfer: "Stalled transfer",
  bottleneck: "Bottleneck",
};
const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { dateStyle: "medium" });
const pct = (n: unknown) => `${Math.round(Number(n) * 100)}%`;

/** The numbers the detector used, in words. */
function numbers(f: Finding): string {
  const e = f.evidence;
  if (f.kind === "transfer_loop")
    return `${e.transfers} transfers in a row between ${f.bureaus.join(" and ")}, none acknowledged; last one ${e.days_unacknowledged} days ago`;
  if (f.kind === "stalled_transfer") return `transferred ${e.days_unacknowledged} days ago, not acknowledged`;
  const of = `of ${e.open} open cases`;
  if (e.measure === "overdue_share") return `${e.overdue} ${of} overdue (${pct(e.share)}, more than ${pct(e.threshold)})`;
  const median = e.median_days_to_close ? ` (${e.median_days_to_close} days)` : "";
  return `${e.older_than_median} ${of} older than the bureau's median days to close${median} (${pct(e.share)}, more than ${pct(e.threshold)})`;
}

function Target({ f }: { f: Finding }) {
  if (f.complaint_id) return <a href={`#/cases/${f.complaint_id}`}>{f.ref}</a>;
  if (f.institution_id) return <a href={`#/institutions/${f.institution_id}`}>{f.institution}</a>;
  const bureau = f.bureaus[0];
  return <a href={`#/cases?${new URLSearchParams({ bureau, overdue: "true" })}`}>{bureau} queue</a>;
}

/** Findings by kind with filters, and the early-warning trend indicator. */
export function FindingsPage({ canDecide, canDetect }: { canDecide: boolean; canDetect: boolean }) {
  const [filters, setFilters] = useState({ kind: "", status: "open", bureau: "" });
  const [message, setMessage] = useState<string | null>(null);
  const query = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
  const { data, error, reload } = useLoad<Finding[]>(`/findings?${query}`);
  const { data: options } = useLoad<Options>("/cases/options");
  const { data: trend } = useLoad<Trend>("/findings/trend");
  const set = (name: keyof typeof filters) => (e: { target: { value: string } }) =>
    setFilters({ ...filters, [name]: e.target.value });

  async function act(path: string, body: unknown, done: (r: never) => string) {
    try {
      setMessage(done(await api<never>(path, body)));
      reload();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }

  return (
    <section>
      <h1>Findings</h1>
      <p>
        Cases that bounce between bureaus without anyone acknowledging them, and queues where too many cases are old
        or overdue. Checked every 5 minutes. A transfer loop or stalled transfer also puts an alert in the Alerts
        screen, where a bureau head or oversight decides whether it is sent.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>
          Kind
          <select value={filters.kind} onChange={set("kind")}>
            <option value="">All</option>
            {Object.entries(KIND).map(([k, label]) => (
              <option key={k} value={k}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={filters.status} onChange={set("status")}>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
            <option value="">All</option>
          </select>
        </label>
        <label>
          Bureau
          <select value={filters.bureau} onChange={set("bureau")}>
            <option value="">All</option>
            {(options?.bureaus ?? []).map((b) => (
              <option key={b.code} value={b.code}>
                {b.code}: {b.name}
              </option>
            ))}
          </select>
        </label>
        {canDetect && (
          <button
            type="button"
            onClick={() =>
              act("/findings/detect", {}, (r: { created: number; resolved: number }) =>
                `${r.created} new, ${r.resolved} no longer holding.`,
              )
            }
          >
            Check now
          </button>
        )}
      </form>
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
      {data && data.length === 0 && <p>No findings match.</p>}
      {data && data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Kind</th>
              <th scope="col">Where</th>
              <th scope="col">Bureaus</th>
              <th scope="col">What the numbers say</th>
              <th scope="col">First seen</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((f) => (
              <tr key={f.id}>
                <td>{f.kind === "bottleneck" ? `Bottleneck (${f.evidence.scope})` : KIND[f.kind]}</td>
                <td>
                  <Target f={f} />
                </td>
                <td>{f.bureaus.join(", ")}</td>
                <td>
                  {numbers(f)}
                  {f.alert_status && (
                    <>
                      <br />
                      <small>Alert: {f.alert_status.replace(/_/g, " ")}</small>
                    </>
                  )}
                </td>
                <td>{day(f.first_seen)}</td>
                <td>
                  {f.status}
                  {f.decided_by && <small> by {f.decided_by}</small>}
                  {canDecide && f.status !== "resolved" && (
                    <>
                      <br />
                      <button
                        type="button"
                        onClick={() =>
                          act(
                            `/findings/${f.id}/decision`,
                            { status: f.status === "open" ? "dismissed" : "open" },
                            () => (f.status === "open" ? "Dismissed. Recorded in the audit log." : "Reopened."),
                          )
                        }
                      >
                        {f.status === "open" ? "Dismiss" : "Reopen"}
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>Trend indicator</h2>
      <p className="note">
        Institutions with more new complaints in the last {trend?.days ?? 30} days than in the {trend?.days ?? 30} days
        before, where the recent ones came to two or more bureaus. These are counts, not a prediction: a rise can have
        many causes. Look at the cases before drawing a conclusion.
      </p>
      {trend && trend.items.length === 0 && <p>No institution shows a rise across bureaus.</p>}
      {trend && trend.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col" className="num">
                Previous {trend.days} days
              </th>
              <th scope="col" className="num">
                Last {trend.days} days
              </th>
              <th scope="col">Bureaus (last {trend.days} days)</th>
            </tr>
          </thead>
          <tbody>
            {trend.items.map((t) => (
              <tr key={t.institution_id}>
                <td>
                  <a href={`#/institutions/${t.institution_id}`}>{t.institution}</a>
                  {t.state && <small> · {t.state}</small>}
                </td>
                <td className="num">{t.previous}</td>
                <td className="num">{t.recent}</td>
                <td>{t.bureaus.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
