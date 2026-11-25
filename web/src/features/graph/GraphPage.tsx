import { useState } from "react";
import { useLoad } from "../../api";
import type { Case, Options } from "../cases/types";
import { day, words } from "../cases/types";
import { type Graph, type GraphEdge, type GraphNode, GraphView, Legend } from "./GraphView";

const KINDS: Record<string, string> = {
  transfer_loop: "Transfer loop",
  stalled_transfer: "Stalled transfer",
  bottleneck: "Bottleneck",
  category_spike: "Category spike",
  deadline_escalation: "Deadline passed",
};

/** The side panel: the node's metadata; for a complaint, its text only if the caller may read the case. */
export function NodePanel({ node, onExpand, expanded = false }: {
  node: GraphNode;
  onExpand?: (institutionId: string) => void;
  expanded?: boolean;
}) {
  return (
    <aside className="panel" aria-label={`Details of ${node.label}`}>
      <h2>{node.label}</h2>
      <p className="note">{words(node.kind)}</p>
      {node.kind === "bureau" && <p>{node.name}: {node.cases} cases shown, {node.open} open.</p>}
      {node.kind === "institution" && (
        <>
          <p>
            {node.state} · {node.cases} cases ({node.open} open, {String(node.overdue)} overdue) in{" "}
            {node.bureaus?.join(", ")}
            {node.multi_bureau && <strong className="flag"> · several bureaus</strong>}
          </p>
          <p>Overlaps among its cases: {node.overlaps?.proposed ?? 0} suggested, {node.overlaps?.approved ?? 0} approved.</p>
          {onExpand && node.institution_id && (
            <button type="button" onClick={() => onExpand(node.institution_id!)}>
              {expanded ? "Hide its complaints" : "Show its complaints"}
            </button>
          )}{" "}
          <a href={`#/institutions/${node.institution_id}`}>Open profile</a>
        </>
      )}
      {node.kind === "complaint" && node.complaint_id && <ComplaintDetail node={node} />}
      {node.findings.length > 0 && (
        <p className="flag">Open findings: {node.findings.map((k) => KINDS[k] ?? k).join(", ")}</p>
      )}
    </aside>
  );
}

function ComplaintDetail({ node }: { node: GraphNode }) {
  const { data } = useLoad<Case>(`/cases/${node.complaint_id}`);
  return (
    <>
      <p>
        {node.bureau} · {words(node.status ?? "")} · {node.category} · filed {node.filed_at ? day(node.filed_at) : "–"}
        {node.overdue ? <strong className="flag"> · overdue</strong> : null}
      </p>
      {data?.readable && data.body ? (
        <p className="complaint">{data.body}</p>
      ) : (
        <p className="note">The text is shown only to the bureau holding the case.</p>
      )}
      <a href={`#/cases/${node.complaint_id}`}>Open case</a>
    </>
  );
}

// Mirrors backend/app/modules/graph/schemas.py Explanation
type EvidenceCase = {
  id: string; ref: string; bureau: string; status: string; filed_at: string; readable: boolean;
  source?: string | null; restricted?: string | null;
};
type Explanation = {
  kind: string; status?: string | null; method: string; confidence: number | null; model: string | null;
  model_version: string | null; similarity?: number | null; reasons: string[]; evidence: EvidenceCase[];
};

/** Why two nodes are linked: method, confidence, model version, and the cases behind it. A case the viewer may not
 *  read shows the restricted marker, never its details. */
export function EdgePanel({ edge, labels, onClose }: {
  edge: GraphEdge; labels: Map<string, string>; onClose: () => void;
}) {
  const q = new URLSearchParams({ source: edge.source, target: edge.target, kind: edge.kind });
  const { data, error } = useLoad<Explanation>(`/graph/explain?${q}`);
  const from = labels.get(edge.source) ?? edge.source;
  const to = labels.get(edge.target) ?? edge.target;
  return (
    <aside className="panel" aria-label={`Why ${from} and ${to} are linked`}>
      <h2>Why linked</h2>
      <p>
        {from} {EDGE_WORDS[edge.kind] ?? edge.kind} {to}
      </p>
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <dl className="evidence">
            <dt>Method</dt>
            <dd>{data.method}</dd>
            <dt>Confidence</dt>
            <dd>{data.confidence === null ? "not rated (an officer decides)" : `${Math.round(data.confidence * 100)}%`}</dd>
            {data.similarity !== null && data.similarity !== undefined && (
              <>
                <dt>Similarity</dt>
                <dd>{data.similarity.toFixed(2)}</dd>
              </>
            )}
            {data.model_version && (
              <>
                <dt>Model</dt>
                <dd>{data.model} {data.model_version}</dd>
              </>
            )}
            {data.status && (
              <>
                <dt>Status</dt>
                <dd>{words(data.status)}</dd>
              </>
            )}
          </dl>
          <p>{data.reasons.join("; ")}.</p>
          <h3>Evidence</h3>
          <ul className="hits">
            {data.evidence.map((c) => (
              <li key={c.id}>
                {c.readable ? <a href={`#/cases/${c.id}`}>{c.ref}</a> : <span>{c.ref}</span>} · {c.bureau} ·{" "}
                {words(c.status)} · filed {day(c.filed_at)}
                {c.readable ? c.source && ` · via ${c.source}` : (
                  <strong className="flag" role="note"> · Links to a restricted record: {c.restricted}</strong>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      <button type="button" onClick={onClose}>Close</button>
    </aside>
  );
}

const EDGE_WORDS: Record<string, string> = {
  holds: "holds cases about",
  about: "complaint about",
  transfer: "transferred cases to",
  overlap_proposed: "suggested overlap with",
  overlap_approved: "confirmed overlap with",
};

/** The same facts as the drawing, as tables (for screen readers, keyboards and print). */
function GraphTable({ graph, onExplain }: { graph: Graph; onExplain: (e: GraphEdge) => void }) {
  const byId = new Map(graph.nodes.map((n) => [n.id, n]));
  const institutions = graph.nodes.filter((n) => n.kind === "institution");
  return (
    <details className="graph-table">
      <summary>The graph as tables ({institutions.length} institutions, {graph.edges.length} connections)</summary>
      <table>
        <caption>Institutions</caption>
        <thead>
          <tr>
            <th scope="col">Institution</th>
            <th scope="col">State</th>
            <th scope="col" className="num">Cases</th>
            <th scope="col" className="num">Open</th>
            <th scope="col">Bureaus</th>
            <th scope="col">Overlaps (suggested, approved)</th>
            <th scope="col">Open findings</th>
            <th scope="col" className="num">Community</th>
          </tr>
        </thead>
        <tbody>
          {institutions.map((n) => (
            <tr key={n.id}>
              <th scope="row">
                <a href={`#/institutions/${n.institution_id}`}>{n.label}</a>
              </th>
              <td>{n.state ?? "–"}</td>
              <td className="num">{n.cases ?? 0}</td>
              <td className="num">{n.open ?? 0}</td>
              <td>{n.bureaus?.join(", ")}</td>
              <td>
                {n.overlaps?.proposed ?? 0}, {n.overlaps?.approved ?? 0}
              </td>
              <td>{n.findings.map((k) => KINDS[k] ?? k).join(", ") || "None"}</td>
              <td className="num">{n.community ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <table>
        <caption>Connections</caption>
        <thead>
          <tr>
            <th scope="col">From</th>
            <th scope="col">Connection</th>
            <th scope="col">To</th>
            <th scope="col" className="num">Count</th>
            <th scope="col" className="num">Confidence</th>
            <th scope="col">Why</th>
          </tr>
        </thead>
        <tbody>
          {graph.edges.map((e) => (
            <tr key={e.id}>
              <td>{byId.get(e.source)?.label ?? e.source}</td>
              <td>{EDGE_WORDS[e.kind] ?? e.kind}</td>
              <td>{byId.get(e.target)?.label ?? e.target}</td>
              <td className="num">{e.count}</td>
              <td className="num">{e.confidence === null || e.confidence === undefined ? "–" : `${Math.round(e.confidence * 100)}%`}</td>
              <td>
                <button type="button" onClick={() => onExplain(e)}
                  aria-label={`Why ${byId.get(e.source)?.label ?? e.source} and ${byId.get(e.target)?.label ?? e.target} are linked`}>
                  Explain
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}

/** Network-wide intelligence graph: every bureau and institution, complaints on request. */
export function GraphPage() {
  const [f, setF] = useState({ state: "", category: "", bureau: "", filed_from: "", filed_to: "", finding_kind: "" });
  const [expand, setExpand] = useState<string[]>([]);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [edge, setEdge] = useState<GraphEdge | null>(null);
  const [byCommunity, setByCommunity] = useState(true);
  const [minConfidence, setMinConfidence] = useState("");
  const { data: options } = useLoad<Options>("/cases/options");
  const query = new URLSearchParams(Object.entries(f).filter(([, v]) => v));
  expand.forEach((id) => query.append("expand", id));
  if (minConfidence) query.set("min_confidence", minConfidence);
  const { data, error } = useLoad<Graph>(`/graph?${query}`);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });
  const toggle = (id: string) => setExpand((xs) => (xs.includes(id) ? xs.filter((x) => x !== id) : [...xs, id]));

  const institutions = (data?.nodes ?? []).filter((n) => n.kind === "institution");
  const clusters = institutions.filter((n) => n.multi_bureau).sort((a, b) => (b.cases ?? 0) - (a.cases ?? 0));
  return (
    <section>
      <h1>Graph</h1>
      <p className="note">
        Bureaus and institutions, joined by the cases each bureau holds; transfers between bureaus; overlaps once an
        institution's complaints are shown. Click a node for details; click an institution, then "Show its complaints".
        Only what your role may see is drawn.
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>State
          <select value={f.state} onChange={set("state")}><option value="">All</option>
            {(options?.states ?? []).map((s) => <option key={s}>{s}</option>)}</select>
        </label>
        <label>Category
          <select value={f.category} onChange={set("category")}><option value="">All</option>
            {(options?.categories ?? []).map((c) => <option key={c}>{c}</option>)}</select>
        </label>
        <label>Bureau
          <select value={f.bureau} onChange={set("bureau")}><option value="">All</option>
            {(options?.bureaus ?? []).map((b) => <option key={b.code}>{b.code}</option>)}</select>
        </label>
        <label>Filed from<input type="date" value={f.filed_from} onChange={set("filed_from")} /></label>
        <label>Filed to<input type="date" value={f.filed_to} onChange={set("filed_to")} /></label>
        <label>With an open finding
          <select value={f.finding_kind} onChange={set("finding_kind")}><option value="">Any or none</option>
            {Object.entries(KINDS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        </label>
        <label>Colour
          <select value={byCommunity ? "community" : "kind"} onChange={(e) => setByCommunity(e.target.value === "community")}>
            <option value="community">by community</option>
            <option value="kind">by kind</option>
          </select>
        </label>
        <label>Overlaps shown
          <select value={minConfidence} onChange={(e) => setMinConfidence(e.target.value)}>
            <option value="">all</option>
            <option value="0.5">confidence 50% or more</option>
            <option value="0.7">confidence 70% or more</option>
            <option value="0.9">confidence 90% or more</option>
          </select>
        </label>
      </form>
      <Legend />
      {byCommunity && (
        <p className="note">
          Colours show communities: groups of bureaus and institutions joined more to each other than to the rest
          (Louvain{data?.build ? `, build ${data.build.version}, ${data.build.communities ?? 0} communities` : ", no build yet"}).
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {data && (
        <div className="graph-layout">
          <GraphView graph={data} onSelect={(n) => (setEdge(null), setSelected(n))} byCommunity={byCommunity}
            onSelectEdge={(e) => (setSelected(null), setEdge(e))}
            label={`Graph of ${institutions.length} institutions; "The graph as tables" below gives the same facts.`} />
          {selected && (
            <NodePanel node={selected} onExpand={toggle}
              expanded={!!selected.institution_id && expand.includes(selected.institution_id)} />
          )}
          {edge && (
            <EdgePanel key={edge.id} edge={edge} labels={new Map(data.nodes.map((n) => [n.id, n.label]))}
              onClose={() => setEdge(null)} />
          )}
        </div>
      )}
      {data && <GraphTable graph={data} onExplain={(e) => (setSelected(null), setEdge(e))} />}
      <h2>Institutions with cases in several bureaus</h2>
      {clusters.length === 0 ? <p>None with these filters.</p> : (
        <ul>
          {clusters.map((n) => (
            <li key={n.id}>
              <a href={`#/institutions/${n.institution_id}`}>{n.label}</a>: {n.cases} cases in {n.bureaus?.join(", ")}
              {n.findings.length > 0 && <strong className="flag"> · {n.findings.map((k) => KINDS[k] ?? k).join(", ")}</strong>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
