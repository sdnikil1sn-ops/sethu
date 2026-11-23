import { useState } from "react";
import { api, useLoad } from "../../api";
import { moment } from "../cases/types";

// Mirrors backend/app/modules/enrichment/schemas.py ReviewItem
type Item = {
  id: string;
  kind: "language" | "ocr" | "translation";
  complaint_id: string;
  ref: string;
  bureau: string;
  attachment_id: string | null;
  reason: string;
  status: "open" | "resolved" | "dismissed";
  created_at: string;
  resolved_at: string | null;
};

const KIND = { language: "Language", ocr: "Reading an attachment", translation: "Translation" };

/** Work for a person where the AI layer was unsure or failed. The holding bureau's officers and heads (and admin)
 *  resolve; oversight reads. */
export function ReviewPage({ canDecide }: { canDecide: boolean }) {
  const [status, setStatus] = useState("open");
  const [message, setMessage] = useState<string | null>(null);
  const { data, error, reload } = useLoad<Item[]>(`/review-items?status=${status}`);

  async function decide(item: Item, decision: "resolved" | "dismissed") {
    try {
      await api(`/review-items/${item.id}/decision`, { status: decision });
      setMessage(`${item.ref}: ${decision}. Recorded in the audit log.`);
      reload();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }

  return (
    <section>
      <h1>Review</h1>
      <p className="note">
        The AI layer only suggests. Where it could not tell the language, read an attachment or translate with enough
        confidence, a person decides: open the case, check the original, and mark the item resolved (you dealt with
        it) or dismissed (nothing needed).
      </p>
      <form className="filters" onSubmit={(e) => e.preventDefault()}>
        <label>
          Show
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </label>
      </form>
      {message && <p role="status">{message}</p>}
      {error && <p role="alert">{error}</p>}
      {data && data.length === 0 && <p>Nothing here.</p>}
      {data && data.length > 0 && (
        <table className="stack" role="table">
          <thead role="rowgroup">
            <tr role="row">
              <th role="columnheader" scope="col">Case</th>
              <th role="columnheader" scope="col">Bureau</th>
              <th role="columnheader" scope="col">What</th>
              <th role="columnheader" scope="col">Why</th>
              <th role="columnheader" scope="col">Since</th>
              {canDecide && status === "open" && <th role="columnheader" scope="col">Decide</th>}
            </tr>
          </thead>
          <tbody role="rowgroup">
            {data.map((i) => (
              <tr role="row" key={i.id}>
                <td role="cell" data-label="Case">
                  <a href={`#/cases/${i.complaint_id}`}>{i.ref}</a>
                </td>
                <td role="cell" data-label="Bureau">{i.bureau}</td>
                <td role="cell" data-label="What">{KIND[i.kind]}</td>
                <td role="cell" data-label="Why">{i.reason}</td>
                <td role="cell" data-label="Since">{moment(i.created_at)}</td>
                {canDecide && status === "open" && (
                  <td role="cell" data-label="Decide">
                    <button type="button" onClick={() => decide(i, "resolved")}
                      aria-label={`Mark ${KIND[i.kind].toLowerCase()} on ${i.ref} resolved`}>
                      Resolved
                    </button>{" "}
                    <button type="button" onClick={() => decide(i, "dismissed")}
                      aria-label={`Dismiss ${KIND[i.kind].toLowerCase()} on ${i.ref}`}>
                      Dismiss
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
