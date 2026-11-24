import { useState } from "react";
import { api, useLoad } from "../../api";

// Mirrors backend/app/modules/ai_health/schemas.py
type Provider = { name: string; path: string; model: string | null; healthy: boolean | null; circuit: string | null };
type Task = { task: string; providers: Provider[]; last_24h: Record<string, number> };
type Metrics = {
  holdout_accuracy: number | null;
  holdout_size: number;
  trained_on?: number;
  corrections?: number;
  mean_confidence?: number | null;
  compared_with?: { version: number | null; holdout_accuracy: number | null };
};
type Health = {
  reporting: boolean;
  reported_at: number | null;
  queue_depth: number | null;
  memory: { loaded: string | null; version: string | null; approx_memory_mb: number; process_rss_mb: number | null } | null;
  models: Record<string, string>;
  tasks: Task[];
  classifier: ({ version: number; created_at: string; embedding_version: string } & Metrics) | null;
  classifier_versions: number;
  embeddings: {
    complaints: number;
    vectors: { model: string; version: string; complaints: number }[];
    active: { model: string; version: string } | null;
  } | null;
};
type Version = {
  version: number;
  status: "active" | "inactive" | "rejected";
  metrics: Metrics;
  embedding_version: string;
  created_at: string;
  created_by: string | null;
};
const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${(x * 100).toFixed(1)}%`);

/** A3: the category classifier (active version, measured accuracy, retrain and roll back) and E5 vector coverage. */
function Classifier({ data, isAdmin, onChanged }: { data: Health; isAdmin: boolean; onChanged: () => void }) {
  const { data: versions, reload } = useLoad<Version[]>("/ai/classifier");
  const [message, setMessage] = useState<string | null>(null);
  async function act(path: string, done: string) {
    try {
      await api(path, {});
      setMessage(done);
      reload();
      onChanged();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }
  const c = data.classifier;
  const e = data.embeddings;
  const active = e?.active && e.vectors.find((v) => v.model === e.active?.model && v.version === e.active?.version);
  return (
    <>
      <h2>Category classifier</h2>
      <p>
        {c
          ? `Version ${c.version} is active (trained ${new Date(c.created_at).toLocaleDateString("en-IN")} on ` +
            `${c.trained_on ?? "?"} examples, ${c.corrections ?? 0} of them officers' corrections). Accuracy on the ` +
            `held-out set: ${pct(c.holdout_accuracy)} of ${c.holdout_size}.`
          : "No classifier yet: categories are suggested by the keyword and glossary rules until E5 is installed."}
      </p>
      <p className="note">
        The held-out set is synthetic seed data, so this figure is not real-world accuracy. A new version is used only
        if it does no worse on the same held-out set; older versions stay for roll-back.
      </p>
      {versions && versions.length > 0 && (
        <table>
          <thead>
            <tr>
              <th scope="col">Version</th>
              <th scope="col">Status</th>
              <th scope="col">Held-out accuracy</th>
              <th scope="col">Trained</th>
              {isAdmin && <th scope="col">Roll back</th>}
            </tr>
          </thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.version}>
                <th scope="row">v{v.version}</th>
                <td>{v.status === "rejected" ? "not used (did worse)" : v.status}</td>
                <td>{pct(v.metrics.holdout_accuracy)}</td>
                <td>
                  {new Date(v.created_at).toLocaleDateString("en-IN")}
                  {v.created_by && ` by ${v.created_by}`}
                </td>
                {isAdmin && (
                  <td>
                    {v.status === "inactive" && (
                      <button type="button" onClick={() => act(`/ai/classifier/${v.version}/activate`, `Version ${v.version} is active.`)}>
                        Use v{v.version}
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h2>Complaint vectors (E5)</h2>
      <p>
        {e?.active
          ? `Active: ${e.active.model} ${e.active.version}; ${active?.complaints ?? 0} of ${e.complaints} complaints ` +
            "have a vector of this version (the rest are embedded in the background, batch by batch)."
          : "No E5 vectors yet: matching uses text similarity only."}
        {e && e.vectors.filter((v) => v !== active).length > 0 &&
          ` Older vectors kept, never compared: ${e.vectors.filter((v) => v !== active).map((v) => `${v.model} ${v.version} (${v.complaints})`).join(", ")}.`}
      </p>
      {isAdmin && (
        <p>
          <button type="button" onClick={() => act("/ai/classifier/retrain", "Training queued on the AI worker.")}>
            Retrain classifier
          </button>{" "}
          <button type="button" onClick={() => act("/ai/reembed", "Re-embedding queued on the AI worker.")}>
            Re-embed now
          </button>
        </p>
      )}
      {message && <p role="status">{message}</p>}
    </>
  );
}

const PATHS = ["primary", "fallback", "last_resort", "human_review"];
const words = (s: string) => s.replace(/_/g, " ");

/** The AI layer at a glance: is the ai-worker reporting, which models pass their checksum, which providers are
 *  healthy and whose circuit is open, and how the last day's items were routed. Admin and oversight only. */
export function AiHealthPage({ isAdmin }: { isAdmin: boolean }) {
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

      <Classifier data={data} isAdmin={isAdmin} onChanged={reload} />

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
