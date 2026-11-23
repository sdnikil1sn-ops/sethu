import { useLoad } from "../../api";

// Mirrors backend/app/modules/ai_health/schemas.py
type Provider = { name: string; path: string; model: string | null; healthy: boolean | null; circuit: string | null };
type Task = { task: string; providers: Provider[]; last_24h: Record<string, number> };
type Health = {
  reporting: boolean;
  reported_at: number | null;
  queue_depth: number | null;
  memory: { loaded: string | null; version: string | null; approx_memory_mb: number; process_rss_mb: number | null } | null;
  models: Record<string, string>;
  tasks: Task[];
};

const PATHS = ["primary", "fallback", "last_resort", "human_review"];
const words = (s: string) => s.replace(/_/g, " ");

/** The AI layer at a glance: is the ai-worker reporting, which models pass their checksum, which providers are
 *  healthy and whose circuit is open, and how the last day's items were routed. Admin and oversight only. */
export function AiHealthPage() {
  const { data, error, reload } = useLoad<Health>("/ai/health");
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading…</p>;
  return (
    <section>
      <h1>AI health</h1>
      <p className="note">
        The AI layer runs inside AICTE's network with no route out. It only suggests: anything it cannot answer
        well enough goes to a person ("human review").{" "}
        <button type="button" onClick={reload}>
          Refresh
        </button>
      </p>
      <p role="status">
        {data.reporting
          ? `The AI worker reported at ${new Date((data.reported_at ?? 0) * 1000).toLocaleTimeString("en-IN")}. ` +
            `Waiting in its queue: ${data.queue_depth ?? "unknown"}. ` +
            `Model in memory: ${data.memory?.loaded ? `${data.memory.loaded} ${data.memory.version}` : "none"}; ` +
            `worker memory ${data.memory?.process_rss_mb ?? "unknown"} MB.`
          : "The AI worker is not reporting (stopped, or starting). Items wait in its queue until it is back."}
      </p>

      <h2>Models</h2>
      {Object.keys(data.models).length === 0 ? (
        <p>No report yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col">Checksum</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.models).map(([name, verdict]) => (
              <tr key={name}>
                <th scope="row">{name}</th>
                <td>{verdict === "ok" ? "Matches the manifest" : <strong className="flag">Refused: {verdict}</strong>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {data.tasks.map((t) => (
        <div key={t.task}>
          <h2>Task {t.task}</h2>
          <table>
            <thead>
              <tr>
                <th scope="col">Order</th>
                <th scope="col">Provider</th>
                <th scope="col">Model</th>
                <th scope="col">Health</th>
                <th scope="col">Circuit</th>
              </tr>
            </thead>
            <tbody>
              {t.providers.map((p) => (
                <tr key={p.name}>
                  <td>{words(p.path)}</td>
                  <th scope="row">{p.name}</th>
                  <td>{p.model ?? "none (rules)"}</td>
                  <td>{p.healthy === null || p.healthy === undefined ? "unknown" : p.healthy ? "Healthy" : <strong className="flag">Unhealthy</strong>}</td>
                  <td>{p.circuit === "open" ? <strong className="flag">open (cooling down)</strong> : words(p.circuit ?? "unknown")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            Last 24 hours:{" "}
            {PATHS.map((path) => `${words(path)} ${t.last_24h[path] ?? 0}`).join(", ")}.
          </p>
        </div>
      ))}
    </section>
  );
}
