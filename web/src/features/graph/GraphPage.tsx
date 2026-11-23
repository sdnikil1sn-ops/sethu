import { useState } from "react";
import { useLoad } from "../../api";
import type { Case, Options } from "../cases/types";
import { day, words } from "../cases/types";
import { type Graph, type GraphNode, GraphView, Legend } from "./GraphView";

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

const EDGE_WORDS: Record<string, string> = {
  holds: "holds cases about",
  about: "complaint about",
  transfer: "transferred cases to",
  overlap_proposed: "suggested overlap with",
  overlap_approved: "confirmed overlap with",
};

/** The same facts as the drawing, as tables (for screen readers, keyboards and print). */
function GraphTable({ graph }: { graph: Graph }) {
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
          </tr>
        </thead>
        <tbody>
          {graph.edges.map((e) => (
            <tr key={e.id}>
              <td>{byId.get(e.source)?.label ?? e.source}</td>
              <td>{EDGE_WORDS[e.kind] ?? e.kind}</td>
              <td>{byId.get(e.target)?.label ?? e.target}</td>
              <td className="num">{e.count}</td>
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
  const { data: options } = useLoad<Options>("/cases/options");
  const query = new URLSearchParams(Object.entries(f).filter(([, v]) => v));
  expand.forEach((id) => query.append("expand", id));
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
      </form>
      <Legend />
      {error && <p role="alert">{error}</p>}
      {data && (
        <div className="graph-layout">
          <GraphView graph={data} onSelect={setSelected}
            label={`Graph of ${institutions.length} institutions; "The graph as tables" below gives the same facts.`} />
          {selected && (
            <NodePanel node={selected} onExpand={toggle}
              expanded={!!selected.institution_id && expand.includes(selected.institution_id)} />
          )}
        </div>
      )}
      {data && <GraphTable graph={data} />}
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
