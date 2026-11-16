import { useLoad } from "../../api";
import type { Finding } from "../findings/Findings";
import type { Profile } from "./types";

// Only the fields used here; mirrors backend/app/modules/overlaps/schemas.py.
type Link = { id: string; status: string; cases: { id: string; ref: string; bureau: string }[] };

const W = 640;
const H = 300;
const CENTRE = { x: W / 2, y: H / 2 };
const RADIUS = 210;
const RED = "#b3261e";

/** Bureaus spread on a circle around the institution; with two, one each side. */
function place(bureaus: string[]) {
  return Object.fromEntries(
    bureaus.map((b, i) => {
      const angle = Math.PI + (2 * Math.PI * i) / bureaus.length;
      return [b, { x: CENTRE.x + RADIUS * Math.cos(angle), y: CENTRE.y + 0.55 * RADIUS * Math.sin(angle) }];
    }),
  );
}

/** A curve from a to b, bent `bend` pixels to one side. Returns the path and its midpoint for a label. */
function curve(a: { x: number; y: number }, b: { x: number; y: number }, bend: number) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2;
  const len = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  const cx = mx - ((b.y - a.y) / len) * bend * 2;
  const cy = my + ((b.x - a.x) / len) * bend * 2;
  return { d: `M${a.x},${a.y} Q${cx},${cy} ${b.x},${b.y}`, x: (mx + cx) / 2, y: (my + cy) / 2 };
}

/** The institution, the bureaus holding its cases, overlap links between them and transfer loops.
 *  Plain SVG; every node and edge is a link. The same facts are listed under the drawing. */
export function RelationshipGraph({ profile }: { profile: Profile }) {
  const { data: links } = useLoad<Link[]>(`/overlaps?institution_id=${profile.id}`);
  const { data: loops } = useLoad<Finding[]>(`/findings?institution_id=${profile.id}&kind=transfer_loop&status=open`);
  if (profile.bureaus.length === 0) return null;

  const at = place(profile.bureaus);
  const count = (b: string) => profile.complaints.filter((c) => c.bureau === b).length;
  const shown = (links ?? []).filter((l) => l.status !== "rejected" && l.cases.length === 2);
  const cases = (b: string) => `#/cases?${new URLSearchParams({ institution_id: profile.id, bureau: b })}`;

  return (
    <figure className="graph">
      <svg viewBox={`0 0 ${W} ${H}`} role="group" aria-label={`Relationships of ${profile.name}`}>
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill={RED} />
          </marker>
        </defs>
        {profile.bureaus.map((b) => (
          <a key={`e-${b}`} href={cases(b)}>
            <title>{`${count(b)} case(s) held by ${b}`}</title>
            <line x1={CENTRE.x} y1={CENTRE.y} x2={at[b].x} y2={at[b].y} className="edge" />
            <text x={(CENTRE.x + at[b].x) / 2} y={(CENTRE.y + at[b].y) / 2 - 6} textAnchor="middle">
              {count(b)} case{count(b) === 1 ? "" : "s"}
            </text>
          </a>
        ))}
        {shown.map((l, i) => {
          const [a, b] = l.cases;
          if (a.bureau === b.bureau) return null;
          const c = curve(at[a.bureau], at[b.bureau], -40 - 22 * i);
          return (
            <a key={l.id} href={`#/cases/${a.id}`}>
              <title>{`Overlap ${l.status === "approved" ? "approved" : "suggested"}: ${a.ref} and ${b.ref}`}</title>
              <path d={c.d} className={`edge overlap-${l.status}`} fill="none" />
              <text x={c.x} y={c.y} textAnchor="middle">
                {a.ref} ↔ {b.ref}
              </text>
            </a>
          );
        })}
        {(loops ?? []).map((f, i) => {
          const [from, to] = f.bureaus;
          if (!at[from] || !at[to]) return null;
          const c = curve(at[from], at[to], 40 + 22 * i);
          const back = curve(at[to], at[from], 40 + 22 * i);
          return (
            <a key={f.id} href={`#/cases/${f.complaint_id}`}>
              <title>{`Transfer loop: ${f.ref} moved ${f.bureaus.join(" and ")} with no acknowledgement`}</title>
              <path d={c.d} stroke={RED} fill="none" strokeWidth={2} markerEnd="url(#arrow)" />
              <path d={back.d} stroke={RED} fill="none" strokeWidth={2} markerEnd="url(#arrow)" />
              <text x={c.x} y={c.y + 14} textAnchor="middle" fill={RED}>
                loop: {f.ref}
              </text>
            </a>
          );
        })}
        <a href={`#/cases?institution_id=${profile.id}`}>
          <title>{`All ${profile.complaints.length} cases at ${profile.name}`}</title>
          <circle cx={CENTRE.x} cy={CENTRE.y} r={34} className="node institution" />
          <text x={CENTRE.x} y={CENTRE.y + 4} textAnchor="middle">
            Institution
          </text>
        </a>
        {profile.bureaus.map((b) => (
          <a key={`n-${b}`} href={cases(b)}>
            <title>{`${b}: open its cases at this institution`}</title>
            <circle cx={at[b].x} cy={at[b].y} r={26} className="node" />
            <text x={at[b].x} y={at[b].y + 4} textAnchor="middle">
              {b}
            </text>
          </a>
        ))}
      </svg>
      <figcaption>
        {profile.bureaus.map((b) => `${b}: ${count(b)} case${count(b) === 1 ? "" : "s"}`).join(" · ")}
        {shown.length > 0 && ` · overlaps: ${shown.map((l) => l.cases.map((c) => c.ref).join(" and ")).join(", ")}`}
        {(loops ?? []).length > 0 && ` · transfer loops: ${(loops ?? []).map((f) => f.ref).join(", ")}`}
        {". "}Dashed: suggested overlap; solid: approved; red arrows: transfer loop.
      </figcaption>
    </figure>
  );
}
