import { useState } from "react";
import { api, useLoad } from "../../api";

// Mirrors backend/app/modules/alerts/schemas.py
type Alert = {
  id: string;
  kind: string;
  status: "pending_approval" | "approved" | "sent" | "rejected" | "failed";
  subject: string;
  body: string;
  recipients: string[];
  missing_recipients: string[];
  cases: string[];
  created_at: string;
  approved_at: string | null;
  approved_by: string | null;
  sent_at: string | null;
  attempts: number;
  last_error: string | null;
  next_attempt_at: string | null;
  can_decide: boolean;
  can_retry: boolean;
};
type AlertPage = { items: Alert[]; mail_inbox_url: string | null };

const STATUS: Record<Alert["status"], string> = {
  pending_approval: "Waiting for approval",
  approved: "Approved, queued to send",
  sent: "Sent",
  rejected: "Rejected",
  failed: "Failed",
};
const moment = (iso: string) => new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

function AlertCard({ alert, onChanged }: { alert: Alert; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "approve" | "reject" | "retry") {
    setBusy(true);
    setError(null);
    try {
      await (decision === "retry"
        ? api(`/alerts/${alert.id}/retry`, {})
        : api(`/alerts/${alert.id}/decision`, { decision }));
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request failed.");
      setBusy(false);
    }
  }

  return (
    <article className="overlap">
      <h3>
        {alert.subject} <small>{STATUS[alert.status]}</small>
      </h3>
      <p>
        Created {moment(alert.created_at)}
        {alert.cases.length > 0 && <> · Cases {alert.cases.join(", ")}</>}
      </p>
      <p className="complaint">{alert.body}</p>
      {alert.status === "sent" && alert.sent_at && (
        <p>
          Sent {moment(alert.sent_at)} to {alert.recipients.join(", ")}.
        </p>
      )}
      {alert.status !== "sent" && <p>To: {alert.recipients.join(", ") || "nobody"}</p>}
      {alert.missing_recipients.length > 0 && (
        <p className="flag" role="status">
          No recipient for {alert.missing_recipients.join(" and ")}: no bureau head there has an e-mail address in
          SETHU. An admin can see who is missing one on the Admin screen.
        </p>
      )}
      {alert.approved_by && alert.approved_at && (
        <p className="note">
          {alert.status === "rejected" ? "Rejected" : "Approved"} by {alert.approved_by} on {moment(alert.approved_at)}.
        </p>
      )}
      {alert.last_error && alert.status !== "sent" && (
        <p className="flag">
          {alert.status === "failed"
            ? "Not sent"
            : `Not delivered yet after ${alert.attempts} attempt${alert.attempts === 1 ? "" : "s"}; next try ${
                alert.next_attempt_at ? moment(alert.next_attempt_at) : "soon"
              }`}
          : {alert.last_error}
        </p>
      )}
      {alert.can_retry && (
        <p>
          <button type="button" disabled={busy} onClick={() => decide("retry")} aria-label={`Retry: ${alert.subject}`}>
            Retry
          </button>{" "}
          <small>Puts it back in the queue with a fresh set of attempts. Recorded in the audit log.</small>
        </p>
      )}
      {alert.can_decide && (
        <p>
          <button type="button" disabled={busy} onClick={() => decide("approve")} aria-label={`Approve and send: ${alert.subject}`}>
            Approve and send
          </button>{" "}
          <button type="button" disabled={busy} onClick={() => decide("reject")} aria-label={`Reject: ${alert.subject}`}>
            Reject
          </button>
        </p>
      )}
      {error && <p role="alert">{error}</p>}
    </article>
  );
}

/** Alerts that concern the signed-in person's bureau (oversight, admin and auditor see all). */
export function AlertsPage() {
  const [status, setStatus] = useState("");
  const { data, error, reload } = useLoad<AlertPage>(`/alerts${status ? `?status=${status}` : ""}`);

  return (
    <section>
      <h1>Alerts</h1>
      <p>
        Emails to bureau heads. Nothing is sent until a person has approved it; approved alerts are sent within a
        minute and listed here with the time and the recipients.
        {data?.mail_inbox_url && (
          <>
            {" "}
            <a href={data.mail_inbox_url} target="_blank" rel="noreferrer">
              Open the local mail inbox
            </a>{" "}
            (development and demo only).
          </>
        )}
      </p>
      <label>
        Show
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All</option>
          {Object.entries(STATUS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <p>
        <button type="button" onClick={reload}>
          Refresh
        </button>
      </p>
      {error && <p role="alert">{error}</p>}
      {data && data.items.length === 0 && <p>No alerts here.</p>}
      {data?.items.map((alert) => <AlertCard key={alert.id + alert.status} alert={alert} onChanged={reload} />)}
    </section>
  );
}
