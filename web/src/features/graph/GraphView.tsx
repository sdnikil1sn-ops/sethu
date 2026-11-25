import type cytoscape from "cytoscape";
import type { Core, ElementDefinition } from "cytoscape";
import { useEffect, useRef } from "react";

// Mirrors backend/app/modules/graph/schemas.py
export type GraphNode = {
  id: string;
  kind: "bureau" | "institution" | "complaint";
  label: string;
  findings: string[];
  name?: string | null;
  cases?: number | null;
  open?: number | null;
  institution_id?: string | null;
  state?: string | null;
  overdue?: number | boolean | null;
  bureaus?: string[] | null;
  multi_bureau?: boolean | null;
  expanded?: boolean | null;
  overlaps?: { proposed: number; approved: number } | null;
  complaint_id?: string | null;
  status?: string | null;
  category?: string | null;
  bureau?: string | null;
  filed_at?: string | null;
  community?: number | null;
};
export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  kind: string;
  count: number;
  confidence?: number | null;
  method?: string | null;
  model_version?: string | null;
};
export type Graph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  expanded_limit: number;
  build?: { version: number; method: string; communities: number | null; created_at: string } | null;
};

// Community colours: distinct in light and dark mode; the community number is also in the table and the panel.
export const COMMUNITY = ["#4f7ccf", "#e0a030", "#6cae75", "#c05fb0", "#3aa6a6", "#d9734f", "#8f7fd6", "#a3a13a"];
export const communityColour = (c: number | null | undefined) =>
  c === null || c === undefined ? "#8a8f98" : COMMUNITY[c % COMMUNITY.length];

export const COLOURS = {
  bureau: "#4f7ccf",
  institution: "#8a8f98",
  multiBureau: "#e0a030",
  finding: "#d9534f",
  complaint: "#6cae75",
  closed: "#5c6066",
  transfer: "#a77bd8",
  overlapSuggested: "#e0703a",
  overlapApproved: "#d9534f",
  holds: "#5c6066",
};

function elements(g: Graph, byCommunity: boolean): ElementDefinition[] {
  return [
    ...g.nodes.map((n) => ({
      data: {
        ...n,
        colour: byCommunity && n.kind !== "complaint" ? communityColour(n.community)
          : n.kind === "bureau" ? COLOURS.bureau : n.kind === "complaint" ? COLOURS.complaint : COLOURS.institution,
        size: n.kind === "bureau" ? 46 : n.kind === "complaint" ? 14 : 16 + Math.min(34, Math.sqrt(n.cases ?? 1) * 5),
        flagged: n.findings.length > 0 ? 1 : 0,
        multi: n.multi_bureau ? 1 : 0,
        closed: n.status === "closed" ? 1 : 0,
      },
    })),
    ...g.edges.map((e) => ({ data: { ...e, width: Math.min(8, 1 + Math.log2(e.count + 1)) } })),
  ];
}

/** The page's own text colour, so labels read in light and dark mode. */
const style = (text: string): cytoscape.Stylesheet[] => [
  { selector: "node", style: { label: "data(label)", "font-size": 9, color: text, "text-valign": "bottom",
      "text-margin-y": 3, width: "data(size)", height: "data(size)", "background-color": "data(colour)",
      "text-wrap": "ellipsis", "text-max-width": "110px" } },
  { selector: "node[kind = 'bureau']", style: { shape: "round-rectangle",
      "font-size": 12, "font-weight": "bold", "text-valign": "center", color: "#fff" } },
  { selector: "node[kind = 'complaint']", style: { "font-size": 7 } },
  { selector: "node[closed = 1]", style: { "background-color": COLOURS.closed } },
  { selector: "node[multi = 1]", style: { "border-width": 4, "border-color": COLOURS.multiBureau } },
  // A halo behind the node (Cytoscape 3.18+; the bundled typings predate these properties).
  { selector: "node[flagged = 1]", style: { "underlay-color": COLOURS.finding, "underlay-padding": 6,
      "underlay-opacity": 0.6, "underlay-shape": "ellipse" } as unknown as cytoscape.Css.Node },
  { selector: "node:selected", style: { "overlay-opacity": 0.25, "overlay-color": "#fff" } },
  { selector: "edge", style: { width: "data(width)", "line-color": COLOURS.holds, "curve-style": "bezier", opacity: 0.6 } },
  { selector: "edge[kind = 'about']", style: { "line-style": "dotted", width: 1 } },
  { selector: "edge[kind = 'transfer']", style: { "line-color": COLOURS.transfer, "line-style": "dashed",
      "target-arrow-shape": "triangle", "target-arrow-color": COLOURS.transfer, opacity: 0.9, label: "data(count)",
      "font-size": 8, color: text } },
  { selector: "edge[kind = 'overlap_proposed']", style: { "line-color": COLOURS.overlapSuggested, "line-style": "dashed",
      width: 2, opacity: 1 } },
  { selector: "edge[kind = 'overlap_approved']", style: { "line-color": COLOURS.overlapApproved, width: 3, opacity: 1 } },
];

/** Cytoscape.js, bundled with the app (no CDN). Redraws when the data changes; reports the node clicked. */
export function GraphView({ graph, onSelect, onSelectEdge, byCommunity = false, height = 520, label }: {
  graph: Graph;
  onSelect: (n: GraphNode | null) => void;
  onSelectEdge?: (e: GraphEdge) => void;
  byCommunity?: boolean;
  height?: number;
  label: string;
}) {
  const box = useRef<HTMLDivElement>(null);
  const cy = useRef<Core | null>(null);
  const select = useRef(onSelect);
  select.current = onSelect;
  const selectEdge = useRef(onSelectEdge);
  selectEdge.current = onSelectEdge;

  useEffect(() => {
    if (!box.current) return;
    let instance: Core | null = null;
    let gone = false;
    // Loaded on demand (its own bundle chunk, served by this app): only the graph screens pay for it.
    import("cytoscape").then(({ default: cytoscape }) => {
      if (gone || !box.current) return;
      instance = cytoscape({ container: box.current, elements: elements(graph, byCommunity),
      style: style(getComputedStyle(box.current).color),
      layout: { name: "cose", animate: false, nodeRepulsion: () => 9000, idealEdgeLength: () => 90, randomize: true,
        fit: true, padding: 30 },
      wheelSensitivity: 0.3, minZoom: 0.1, maxZoom: 4 });
      instance.on("tap", "node", (e) => select.current(e.target.data() as GraphNode));
      instance.on("tap", "edge", (e) => selectEdge.current?.(e.target.data() as GraphEdge));
      instance.on("tap", (e) => e.target === instance && select.current(null));
      cy.current = instance;
      instance.one("layoutstop", () => instance?.fit(undefined, 30));
      instance.fit(undefined, 30);
    });
    return () => {
      gone = true;
      instance?.destroy();
    };
  }, [graph, byCommunity]);

  return <div ref={box} className="cy" style={{ height }} role="img" aria-label={label} />;
}

/** What the colours mean. */
export function Legend() {
  const swatch = (colour: string, round = true) => (
    <span aria-hidden style={{ display: "inline-block", width: 12, height: 12, borderRadius: round ? 6 : 2,
      background: colour, marginRight: 4, verticalAlign: "middle" }} />
  );
  // Line samples are drawn, not typed: coloured text glyphs failed the contrast check, and the words carry the meaning.
  const line = (colour: string, style: "dashed" | "solid", width = 2) => (
    <span aria-hidden style={{ display: "inline-block", width: 22, borderTop: `${width}px ${style} ${colour}`,
      marginRight: 4, verticalAlign: "middle" }} />
  );
  return (
    <p className="note">
      {swatch(COLOURS.bureau, false)}bureau {swatch(COLOURS.institution)}institution (size: cases){" "}
      {swatch(COLOURS.multiBureau, false)}ring: cases in several bureaus{" "}
      {swatch(COLOURS.finding, false)}halo: open finding {swatch(COLOURS.complaint)}open complaint{" "}
      {swatch(COLOURS.closed)}closed {line(COLOURS.transfer, "dashed")}transfers{" "}
      {line(COLOURS.overlapSuggested, "dashed")}suggested overlap{" "}
      {line(COLOURS.overlapApproved, "solid", 3)}approved overlap
    </p>
  );
}
