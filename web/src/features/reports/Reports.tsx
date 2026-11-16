import { useState } from "react";
import { download, useLoad } from "../../api";

// Mirrors backend/app/modules/reports/schemas.py
type Report = {
  name: string;
  title: string;
  scope: string;
  columns: { key: string; label: string }[];
  rows: Record<string, string | number | null>[];
};

const REPORTS = [
  ["institutions", "Complaints by institution"],
  ["bureaus", "Bureau performance"],
  ["overlaps", "Overlap outcomes"],
] as const;
const NUMERIC = new Set(["cases", "open", "overdue", "bureaus", "filed", "closed", "median_days_to_close",
  "suggested", "approved", "rejected", "pending", "alerts_sent"]);
const NOTES: Record<string, string> = {
  institutions:
    "Cases filed in the range. Open and overdue are as of now. “Bureaus with cases” counts every bureau holding a case there, including ones whose cases you cannot see.",
  bureaus:
    "Filed: cases filed in the range. Closed and median days to close: cases closed in the range. Overdue: of the cases filed in the range, those past their deadline now.",
  overlaps: "Overlap suggestions made in the range and what became of them, by pair of bureaus.",
};

/** Three reports over a date range, each exportable as CSV. Exports are recorded in the audit log. */
export function ReportsPage() {
  const [name, setName] = useState<string>("institutions");
  const [range, setRange] = useState({ date_from: "", date_to: "" });
  const [exporting, setExporting] = useState<{ busy: boolean; error?: string; done?: string }>({ busy: false });
  const params = new URLSearchParams(Object.entries(range).filter(([, v]) => v));
  const { data, error } = useLoad<Report>(`/reports/${name}${params.toString() ? `?${params}` : ""}`);

  async function exportCsv() {
    setExporting({ busy: true });
    try {
      await download(`/reports/${name}/export${params.toString() ? `?${params}` : ""}`);
      setExporting({ busy: false, done: "Exported. The export is recorded in the audit log." });
    } catch (e) {
      setExporting({ busy: false, error: e instanceof Error ? e.message : "The export failed." });
    }
  }

  return (
    <section>
      <h1>Reports</h1>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>
          Report
          <select value={name} onChange={(e) => (setName(e.target.value), setExporting({ busy: false }))}>
            {REPORTS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          From
          <input type="date" value={range.date_from} onChange={(e) => setRange({ ...range, date_from: e.target.value })} />
        </label>
        <label>
          To
          <input type="date" value={range.date_to} onChange={(e) => setRange({ ...range, date_to: e.target.value })} />
        </label>
        <button type="button" onClick={exportCsv} disabled={exporting.busy || !data}>
          {exporting.busy ? "Exporting…" : "Export CSV"}
        </button>
      </form>
      <div aria-live="polite">
        {exporting.done && <p role="status">{exporting.done}</p>}
        {exporting.error && <p role="alert">{exporting.error}</p>}
      </div>
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <h2>
            {data.title} <small>{data.scope}</small>
          </h2>
          <p className="note">{NOTES[data.name]}</p>
          {data.rows.length === 0 ? (
            <p>Nothing in this range.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  {data.columns.map((c) => (
                    <th key={c.key} scope="col" className={NUMERIC.has(c.key) ? "num" : undefined}>
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, i) => (
                  <tr key={i}>
                    {data.columns.map((c) => (
                      <td key={c.key} className={NUMERIC.has(c.key) ? "num" : undefined}>
                        {c.key === "institution" && row.institution_id ? (
                          <a href={`#/institutions/${row.institution_id}`}>{row.institution}</a>
                        ) : (
                          (row[c.key] ?? "–")
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
