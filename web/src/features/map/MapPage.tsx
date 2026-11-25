import { useEffect, useRef, useState } from "react";
import { api, useLoad } from "../../api";
import { day, words } from "../cases/types";

// Mirrors backend/app/modules/signals/schemas.py
type StateRow = {
  state: string; map_name: string | null; complaints: number; open: number; recent: number; institutions: number;
  signals: number;
};
type MapStates = { recent_days: number; label: string; states: StateRow[] };
type Member = {
  id: string; ref: string; bureau: string; state: string | null; category: string | null; filed_at: string;
  readable: boolean; restricted?: string | null;
};
export type Signal = {
  id: string; label: string; category_group: string; categories: string[]; states: string[]; window_start: string;
  window_end: string; method: "dbscan" | "zscore" | "ratio"; path: string; score: number | null; members: number;
  explanation: Record<string, unknown> & { why?: string }; parameters: Record<string, number>;
  status: "new" | "acknowledged" | "dismissed" | "actioned"; status_reason: string | null; decided_at: string | null;
  decided_by: string | null; first_seen: string; last_seen: string; bureaus: string[]; cases: Member[];
};
type StateDetail = {
  state: string;
  institutions: { id: string; name: string; district: string | null; complaints: number; open: number }[];
  signals: Signal[];
};

const METHOD = {
  dbscan: "clustering in place and time (DBSCAN)",
  zscore: "weekly counts against the 90-day baseline (Z-score)",
  ratio: "count against the baseline (ratio)",
};
const STATUS = { new: "New", acknowledged: "Acknowledged", dismissed: "Dismissed", actioned: "Linked to action" };

/** One signal: what was found, how, the cases behind it (restricted ones marked), and the decision buttons. */
export function SignalCard({ s, canDecide, onChanged }: { s: Signal; canDecide: boolean; onChanged: () => void }) {
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  async function decide(status: "acknowledged" | "dismissed" | "actioned") {
    try {
      await api(`/signals/${s.id}/decision`, { status, reason: reason || null });
      setMessage(`${STATUS[status]}. Recorded in the audit log.`);
      onChanged();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }
  return (
    <article className="overlap">
      <h3>
        {s.label}: {s.category_group} in {s.states.join(", ")} <small>{STATUS[s.status]}</small>
      </h3>
      <p>{s.explanation.why}.</p>
      <dl className="evidence">
        <dt>Found by</dt>
        <dd>{METHOD[s.method]} ({words(s.path)} method)</dd>
        <dt>Window</dt>
        <dd>{day(s.window_start)} to {day(s.window_end)}</dd>
        <dt>Score</dt>
        <dd>{s.score ?? "–"}</dd>
        <dt>Parameters</dt>
        <dd>{Object.entries(s.parameters).map(([k, v]) => `${words(k)} ${v}`).join(", ")}</dd>
        <dt>Bureaus</dt>
        <dd>{s.bureaus.join(", ")}</dd>
      </dl>
      <details>
        <summary>The {s.members} cases in it</summary>
        <ul className="hits">
          {s.cases.map((c) => (
            <li key={c.id}>
              {c.readable ? <a href={`#/cases/${c.id}`}>{c.ref}</a> : <span>{c.ref}</span>} · {c.bureau} · {c.state} ·{" "}
              {c.category} · filed {day(c.filed_at)}
              {!c.readable && <strong className="flag" role="note"> · Restricted record: {c.restricted}</strong>}
            </li>
          ))}
        </ul>
      </details>
      {s.status_reason && <p className="note">Reason: {s.status_reason}</p>}
      {canDecide && s.status !== "dismissed" && (
        <p>
          <label>
            Reason (needed to dismiss)
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={500} />
          </label>{" "}
          {s.status === "new" && <button type="button" onClick={() => decide("acknowledged")}>Acknowledge</button>}{" "}
          <button type="button" onClick={() => decide("actioned")}>Linked to action</button>{" "}
          <button type="button" disabled={!reason.trim()} onClick={() => decide("dismissed")}>Dismiss</button>
        </p>
      )}
      {message && <p role="status">{message}</p>}
    </article>
  );
}

type GeoJSON = { type: string; features: { properties: { name: string } }[]; source?: { attribution?: string } };

/** ECharts, bundled with the app and loaded only here; the boundaries come from this app's own server. */
function IndiaMap({ states, onPick }: { states: StateRow[]; onPick: (state: string) => void }) {
  const box = useRef<HTMLDivElement>(null);
  const [attribution, setAttribution] = useState<string | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const pick = useRef(onPick);
  pick.current = onPick;
  useEffect(() => {
    let chart: { dispose: () => void; resize: () => void } | null = null;
    let gone = false;
    const resize = () => chart?.resize();
    Promise.all([
      fetch(new URL("maps/india-states.json", document.baseURI)).then((r) => {   // this app's own server
        if (!r.ok) throw new Error(`map data: ${r.status}`);
        return r.json() as Promise<GeoJSON>;
      }),
      import("./echarts"),
    ]).then(([geo, echarts]) => {
      if (gone || !box.current) return;
      setAttribution(geo.source?.attribution ?? null);
      echarts.registerMap("india", geo as never);
      const byName = new Map(states.filter((s) => s.map_name).map((s) => [s.map_name!, s]));
      const max = Math.max(1, ...states.map((s) => s.complaints));
      const instance = echarts.init(box.current, undefined, { renderer: "canvas" });
      instance.setOption({
        tooltip: {
          trigger: "item",
          formatter: (p: { name: string }) => {
            const s = byName.get(p.name);
            return s ? `${p.name}: ${s.complaints} complaints (${s.open} open), ${s.signals} signal(s)` : `${p.name}: no complaints`;
          },
        },
        visualMap: { min: 0, max, text: ["More complaints", "Fewer"], calculable: false, left: 8, bottom: 8,
          inRange: { color: ["#e8eef8", "#4f7ccf", "#1d3f7a"] } },
        series: [{
          type: "map", map: "india", roam: true, scaleLimit: { min: 1, max: 2 }, selectedMode: false,
          emphasis: { label: { show: true } },
          data: geo.features.map((f) => {
            const s = byName.get(f.properties.name);
            return { name: f.properties.name, value: s?.complaints ?? 0,
              itemStyle: s?.signals ? { borderColor: "#d9534f", borderWidth: 2.5 } : undefined };
          }),
        }],
      });
      instance.on("click", (p: { name: string }) => {
        const s = byName.get(p.name);
        if (s) pick.current(s.state);
      });
      chart = instance;
      window.addEventListener("resize", resize);
    }).catch((e: unknown) => setFailed(e instanceof Error ? e.message : "the map could not be drawn"));
    return () => {
      gone = true;
      window.removeEventListener("resize", resize);
      chart?.dispose();
    };
  }, [states]);
  return (
    <>
      <div ref={box} className="india-map" role="img"
        aria-label="Map of India: states shaded by number of complaints, red outline where there is a signal. The table below gives the same facts." />
      {failed && <p role="alert">The map could not be drawn ({failed}); the table below has the same facts.</p>}
      <p className="note">
        Boundaries: {attribution ?? "DataMeet India community (CC BY 4.0)"}. Shown for orientation only; to be checked
        against the Survey of India's official depiction before any public use.
      </p>
    </>
  );
}

/** India map of complaint density and emerging signals; state -> institutions and signals -> cases. */
export function MapPage({ canDecide }: { canDecide: boolean }) {
  const { data, error, reload } = useLoad<MapStates>("/map/states");
  const [state, setState] = useState<string | null>(null);
  const [status, setStatus] = useState("new");
  const signals = useLoad<Signal[]>(`/signals${status ? `?status=${status}` : ""}`);
  return (
    <section>
      <h1>Map and signals</h1>
      <p className="note">
        Complaint density by state and {data?.label ?? "emerging signals"}: patterns in the numbers, found by
        clustering in place and time or by comparison with each state's recent past. A signal is not a finding: a
        person verifies it, then acknowledges, links it to action or dismisses it with a reason.
      </p>
      {error && <p role="alert">{error}</p>}
      {data && <IndiaMap states={data.states} onPick={setState} />}
      {data && (
        <table>
          <caption>Complaints and signals by state (the same facts as the map; choose a state to see more)</caption>
          <thead>
            <tr>
              <th scope="col">State</th>
              <th scope="col" className="num">Complaints</th>
              <th scope="col" className="num">Open</th>
              <th scope="col" className="num">Last {data.recent_days} days</th>
              <th scope="col" className="num">Institutions</th>
              <th scope="col" className="num">Signals</th>
              <th scope="col">Details</th>
            </tr>
          </thead>
          <tbody>
            {data.states.map((s) => (
              <tr key={s.state}>
                <th scope="row">{s.state}</th>
                <td className="num">{s.complaints}</td>
                <td className="num">{s.open}</td>
                <td className="num">{s.recent}</td>
                <td className="num">{s.institutions}</td>
                <td className="num">{s.signals ? <strong className="flag">{s.signals}</strong> : 0}</td>
                <td>
                  <button type="button" onClick={() => setState(s.state)} aria-label={`Show ${s.state}`}>Show</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {state && <StatePanel key={state} state={state} canDecide={canDecide} onChanged={() => (reload(), signals.reload())} />}
      <h2>Signals</h2>
      <label>
        Show
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="new">New</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="actioned">Linked to action</option>
          <option value="dismissed">Dismissed</option>
          <option value="">All</option>
        </select>
      </label>
      {signals.error && <p role="alert">{signals.error}</p>}
      {signals.data && signals.data.length === 0 && <p>None.</p>}
      {signals.data?.map((s) => (
        <SignalCard key={s.id + s.status} s={s} canDecide={canDecide} onChanged={() => (reload(), signals.reload())} />
      ))}
    </section>
  );
}

function StatePanel({ state, canDecide, onChanged }: { state: string; canDecide: boolean; onChanged: () => void }) {
  const { data, error, reload } = useLoad<StateDetail>(`/map/state?state=${encodeURIComponent(state)}`);
  return (
    <section aria-labelledby="state-detail">
      <h2 id="state-detail">{state}</h2>
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <h3>Institutions</h3>
          {data.institutions.length === 0 ? <p>None.</p> : (
            <ul className="hits">
              {data.institutions.map((i) => (
                <li key={i.id}>
                  <a href={`#/institutions/${i.id}`}>{i.name}</a> {i.district && `(${i.district})`}: {i.complaints}{" "}
                  complaints, {i.open} open
                </li>
              ))}
            </ul>
          )}
          <h3>Signals here</h3>
          {data.signals.length === 0 ? <p>None.</p> : data.signals.map((s) => (
            <SignalCard key={s.id + s.status} s={s} canDecide={canDecide} onChanged={() => (reload(), onChanged())} />
          ))}
        </>
      )}
    </section>
  );
}
