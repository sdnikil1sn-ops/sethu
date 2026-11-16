import { useLoad } from "../../api";
import { type Action, type Timeline, describe, moment } from "./types";

/** A transfer nobody accepted: the same case was passed on again, or nothing followed at all. */
function unacknowledged(actions: Action[], n: number): boolean {
  const a = actions[n];
  if (a.action !== "transferred" || a.acknowledged_at) return false;
  const next = actions.slice(n + 1).find((b) => b.ref === a.ref && ["acknowledged", "transferred"].includes(b.action));
  return next?.action !== "acknowledged";
}

/** Action history, oldest first. Read-only: entries can never be edited or removed. */
export function History({ actions, showCase = false }: { actions: Action[]; showCase?: boolean }) {
  if (actions.length === 0) return <p>No history to show.</p>;
  return (
    <ol className="history">
      {actions.map((a, n) => (
        <li key={a.id}>
          <time dateTime={a.created_at}>{moment(a.created_at)}</time>
          <div>
            <strong>
              {showCase && `${a.ref}: `}
              {describe(a)}
            </strong>
            {unacknowledged(actions, n) && <span className="flag"> not acknowledged</span>}
            {a.actor && <> by {a.actor}</>}
            {a.note && <p>{a.note}</p>}
          </div>
        </li>
      ))}
    </ol>
  );
}

/** Every action on an institution's cases that the signed-in person may read. */
export function InstitutionTimeline({ institutionId }: { institutionId: string }) {
  const { data, error } = useLoad<Timeline>(`/cases/timeline?institution_id=${institutionId}`);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading…</p>;
  return (
    <>
      <History actions={data.actions} showCase />
      {data.hidden_cases > 0 && (
        <p className="note">
          {data.hidden_cases} case{data.hidden_cases === 1 ? "" : "s"} held by another bureau: the history is visible
          to that bureau only.
        </p>
      )}
    </>
  );
}
