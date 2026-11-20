import type { Dna } from "./types";

const pct = (n: number) => `${Math.round(n * 100)}%`;
const TREND = { up: "Rising", down: "Falling", flat: "Steady" };

/** Profile DNA: six measures from case summaries. Counts only; no complaint text. */
export function DnaPanel({ dna }: { dna: Dna }) {
  const {
    category_mix: mix,
    volume,
    recurrence,
    disposal,
    bureaus,
    trend,
  } = dna;
  return (
    <section className="dna" aria-labelledby="dna-title">
      <h2 id="dna-title">Profile DNA</h2>
      <dl className="tiles">
        <div>
          <dt>Category mix</dt>
          <dd>
            {mix.length === 0 ? (
              "No cases"
            ) : (
              <ul className="bars">
                {mix.slice(0, 5).map((c) => (
                  <li key={c.category}>
                    <span>{c.category}</span>
                    <span
                      className="bar"
                      style={{ width: pct(c.share) }}
                      aria-hidden="true"
                    />
                    <small>
                      {c.cases} ({pct(c.share)})
                    </small>
                  </li>
                ))}
                {mix.length > 5 && (
                  <li>
                    <small>and {mix.length - 5} more</small>
                  </li>
                )}
              </ul>
            )}
          </dd>
        </div>
        <div>
          <dt>Volume</dt>
          <dd>
            {volume.total} cases
            <small>
              <br />
              {volume.last_12_months} in the last 12 months, about{" "}
              {volume.per_month} a month
            </small>
          </dd>
        </div>
        <div>
          <dt>Recurrence</dt>
          <dd>
            {recurrence.repeat_cases} repeat
            {recurrence.repeat_cases === 1 ? "" : "s"} ({pct(recurrence.share)})
            <small>
              <br />
              {recurrence.repeat_cases === 0
                ? `No category raised twice within ${recurrence.window_days} days`
                : `Same category within ${recurrence.window_days} days: ${recurrence.categories.join(", ")}`}
            </small>
          </dd>
        </div>
        <div>
          <dt>Disposal time</dt>
          <dd>
            {disposal.median_days === null
              ? "None closed yet"
              : `${disposal.median_days} days`}
            <small>
              <br />
              median from filing to closing, {disposal.closed} closed
            </small>
          </dd>
        </div>
        <div>
          <dt>Bureaus involved</dt>
          <dd>
            {bureaus.length}
            <small>
              <br />
              {bureaus.map((b) => `${b.bureau}: ${b.cases}`).join(" · ") ||
                "None"}
            </small>
          </dd>
        </div>
        <div>
          <dt>Trend</dt>
          <dd>
            {TREND[trend.direction]}
            <small>
              <br />
              {trend.recent} in the last {trend.window_days} days,{" "}
              {trend.previous} in the {trend.window_days} before
            </small>
          </dd>
        </div>
      </dl>
    </section>
  );
}
