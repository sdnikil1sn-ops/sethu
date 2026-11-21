import { useState } from "react";
import { useLoad } from "../../api";
import { NodePanel } from "../graph/GraphPage";
import { type Graph, type GraphNode, GraphView, Legend } from "../graph/GraphView";
import type { Profile } from "./types";

/** The institution's corner of the network graph (the Graph screen, scoped and expanded): its bureaus, its
 *  complaints as nodes, the cases each bureau holds, transfers between those bureaus and overlap links. */
export function RelationshipGraph({ profile }: { profile: Profile }) {
  const { data } = useLoad<Graph>(`/graph?institution_id=${profile.id}&expand=${profile.id}`);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  if (!data) return null;
  const links = data.edges.filter((e) => e.kind.startsWith("overlap_"));
  const bureaus = data.nodes.filter((n) => n.kind === "bureau" && (n.cases ?? 0) > 0).map((n) => n.label);
  return (
    <figure className="graph">
      <Legend />
      <div className="graph-layout">
        <GraphView graph={data} onSelect={setSelected} height={360}
          label={`Relationships of ${profile.name}; the caption gives the same facts.`} />
        {selected && <NodePanel node={selected} />}
      </div>
      <figcaption>
        {data.nodes.filter((n) => n.kind === "complaint").length} complaints held by {bureaus.join(", ")};{" "}
        {links.filter((e) => e.kind === "overlap_approved").length} approved and{" "}
        {links.filter((e) => e.kind === "overlap_proposed").length} suggested overlap links you may see.{" "}
        <a href={`#/graph`}>Open the network graph</a>
      </figcaption>
    </figure>
  );
}
