import { useState } from "react";
import { api, useLoad } from "../../api";
import { type Page, Pager } from "../../Pager";
import type { Options } from "../cases/types";

// Mirrors backend/app/modules/overlaps/schemas.py
type LinkedCase = { id: string; ref: string; bureau: string; status: string; filed_at: string };
// The evidence stored with a suggestion (A3). Older suggestions carry only trigram/semantic/fired.
type Signals = {
  method?: "e5" | "text" | "officer";
  similarity?: number | null;
  confidence?: number | null;
  agreement?: "agree" | "disagree" | "not compared" | null;
  trigram?: number;
  semantic?: number | null;
  same_language?: boolean;
  model?: string | null;
  model_version?: string | null;
  thresholds?: { e5: number; trigram: number };
};
type Link = {
  id: string;
  score: number | null;
  reasons: string[];
  signals: Signals;
  status: "proposed" | "approved" | "rejected";
  decided_at: string | null;
  decided_by: string | null;
  institution_id: string | null;
  institution: string | null;
  category: string | null;
  cases: LinkedCase[];
  can_decide: boolean;
  alert_status: string | null;
  alert_recipients: string[] | null;
};
type Tier1 = {
  institution_id: string;
  institution: string;
  state: string | null;
  bureaus: string[];
  cases: { id: string; ref: string; bureau: string; category: string | null }[];
  tier2_pairs: number;
};

export const BANNER = "Potential Overlapping Cases – Coordination Required";
const STATUS = { proposed: "Suggested", approved: "Approved", rejected: "Rejected" };
const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { dateStyle: "medium" });
const METHOD = {
  e5: "Meaning similarity (E5 model, works across languages)",
  text: "Text similarity (trigram fallback, same language only)",
  officer: "No confident answer: shown for an officer to judge",
};

/** How the suggestion was made, and how sure the system is. */
function Explanation({ s }: { s: Signals }) {
  if (!s.method) return null;
  const pct = (x: number | null | undefined) => (x === null || x === undefined ? "–" : `${Math.round(x * 100)}%`);
  return (
    <dl className="evidence">
      <dt>Matched by</dt>
      <dd>{METHOD[s.method]}</dd>
      <dt>Matching confidence</dt>
      <dd>{s.confidence === null || s.confidence === undefined ? "not rated (officer review)" : pct(s.confidence)}</dd>
      <dt>Similarity</dt>
      <dd>
        meaning {s.semantic === null || s.semantic === undefined ? "not available" : s.semantic.toFixed(2)}
        {s.thresholds && ` (threshold ${s.thresholds.e5})`}; text {s.trigram?.toFixed(2)}
        {s.thresholds && ` (threshold ${s.thresholds.trigram})`}
        {s.same_language === false && "; different languages, so text similarity is not used"}
      </dd>
      {s.agreement && s.agreement !== "not compared" && (
        <>
          <dt>Signals</dt>
          <dd>{s.agreement === "agree" ? "agree (confidence raised)" : "disagree (confidence lowered)"}</dd>
        </>
      )}
      {s.model_version && (
        <>
          <dt>Model</dt>
          <dd>
            {s.model} {s.model_version}
          </dd>
        </>
      )}
    </dl>
  );
}

function LinkCard({ link, onChanged }: { link: Link; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "approve" | "reject") {
    setBusy(true);
    setError(null);
    try {
      await api(`/overlaps/${link.id}/decision`, { decision });
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request failed.");
      setBusy(false);
    }
  }

  const refs = link.cases.map((c) => c.ref).join(" and ");
  return (
    <article className="overlap">
      <h3>
        {refs} <small>{STATUS[link.status]}</small>
      </h3>
      <p>
        {link.institution_id ? <a href={`#/institutions/${link.institution_id}`}>{link.institution}</a> : "Institution not matched"}
        {link.category && <> · {link.category}</>}
      </p>
      <div className="pair">
        {link.cases.map((c) => (
          <div key={c.id}>
            <a href={`#/cases/${c.id}`}>{c.ref}</a>
            <br />
            {c.bureau} · {c.status.replace(/_/g, " ")} · filed {day(c.filed_at)}
          </div>
        ))}
      </div>
      <p>Why: {link.reasons.join("; ")}.</p>
      <Explanation s={link.signals ?? {}} />
      {link.status === "proposed" && !link.can_decide && (
        <p className="note">Waiting for an officer or head of {link.cases.map((c) => c.bureau).join(" or ")} to decide.</p>
      )}
      {link.status !== "proposed" && (
        <p className="note">
          {STATUS[link.status]} by {link.decided_by ?? "someone"}
          {link.decided_at && ` on ${day(link.decided_at)}`}.
          {link.alert_recipients &&
            ` Alert to ${link.alert_recipients.join(", ")}: ${link.alert_status === "sent" ? "sent" : "queued"}.`}
        </p>
      )}
      {link.can_decide && (
        <p>
          <button type="button" disabled={busy} onClick={() => decide("approve")} aria-label={`Approve link between ${refs}`}>
            Approve link
          </button>{" "}
          <button type="button" disabled={busy} onClick={() => decide("reject")} aria-label={`Reject link between ${refs}`}>
            Not the same matter
          </button>
          <br />
          <small>Approving queues an alert to the heads of both bureaus. Either choice is recorded in the audit log.</small>
        </p>
      )}
      {error && <p role="alert">{error}</p>}
    </article>
  );
}

/** Tier 2 links the signed-in person may see. With `institutionId`, only that institution's. */
export function Links({ institutionId, status, bureau }: { institutionId?: string; status?: string; bureau?: string }) {
  const query = new URLSearchParams();
  if (institutionId) query.set("institution_id", institutionId);
  if (status) query.set("status", status);
  if (bureau) query.set("bureau", bureau);
  const [page, setPage] = useState({ limit: 50, offset: 0 });
  query.set("limit", String(page.limit));
  query.set("offset", String(page.offset));
  const { data, error, reload } = useLoad<Page<Link>>(`/overlaps?${query}`);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading…</p>;
  if (data.items.length === 0 && page.offset === 0) return institutionId ? null : <p>Nothing here.</p>;
  return (
    <>
      {institutionId && data.items.some((l) => l.status !== "rejected") && (
        <p role="status" className="banner">
          {BANNER}
        </p>
      )}
      {data.items.map((link) => (
        <LinkCard key={link.id + link.status} link={link} onChanged={reload} />
      ))}
      {(data.has_next || page.offset > 0 || !institutionId) && (
        <Pager page={data} noun="overlap suggestions" onChange={(limit, offset) => setPage({ limit, offset })} />
      )}
    </>
  );
}

/** Tier 1 note for one institution: open cases in more than one bureau. */
export function SameInstitution({ institutionId }: { institutionId: string }) {
  const { data } = useLoad<Tier1[]>(`/overlaps/tier1?institution_id=${institutionId}`);
  const found = data?.[0];
  if (!found) return null;
  return (
    <p role="status">
      Same institution, {found.bureaus.length} bureaus: {found.bureaus.join(" and ")} each hold open cases here (
      {found.cases.map((c) => `${c.ref} ${c.bureau}`).join(", ")}).
    </p>
  );
}

export function OverlapsPage({ canDetect }: { canDetect: boolean }) {
  const [status, setStatus] = useState("proposed");
  const [bureau, setBureau] = useState("");
  const { data: options } = useLoad<Options>("/cases/options");
  const [message, setMessage] = useState<string | null>(null);
  const [round, setRound] = useState(0);
  const { data: tier1, error } = useLoad<Tier1[]>("/overlaps/tier1");
  const shown = tier1?.filter((t) => !bureau || t.bureaus.includes(bureau));

  async function detect() {
    // Queued to the worker (it runs the model); poll until it reports, for up to two minutes.
    try {
      const { task_id } = await api<{ task_id: string }>("/overlaps/detect", {});
      setMessage("Queued: the worker is looking for new overlaps…");
      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const s = await api<{ state: string; suggested: number | null; skipped: boolean }>(`/overlaps/detect/${task_id}`);
        if (s.state === "SUCCESS" && s.skipped) {
          setMessage("A search was already running; its suggestions will appear here when it finishes.");
          return;
        }
        if (s.state === "SUCCESS") {
          setMessage(`${s.suggested ?? 0} new suggestion${s.suggested === 1 ? "" : "s"}.`);
          setRound((r) => r + 1);
          return;
        }
        if (s.state === "FAILURE") {
          setMessage("The worker could not finish the search; it will run again on its schedule.");
          return;
        }
      }
      setMessage("Still running; new suggestions will appear here when the worker finishes.");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }

  return (
    <section>
      <h1>Overlaps</h1>
      <h2>Same matter in two bureaus</h2>
      <p>
        Two open cases in different bureaus about the same institution and category, filed within 30 days, that say
        the same thing, in any language. Each suggestion explains how it was found and how sure the system is. The
        system only suggests; an officer or head of either bureau decides.
      </p>
      <label>
        Show
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="proposed">Suggested, waiting for a decision</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="">All</option>
        </select>
      </label>{" "}
      <label>
        Bureau
        <select value={bureau} onChange={(e) => setBureau(e.target.value)}>
          <option value="">All</option>
          {(options?.bureaus ?? []).map((b) => (
            <option key={b.code} value={b.code}>
              {b.code}: {b.name}
            </option>
          ))}
        </select>
      </label>{" "}
      {canDetect && (
        <button type="button" onClick={detect}>
          Look for new overlaps now
        </button>
      )}
      {message && <p role="status">{message}</p>}
      <Links key={`${status}${bureau}${round}`} status={status || undefined} bureau={bureau || undefined} />

      <h2>Same institution in two bureaus</h2>
      <p>
        Institutions where more than one bureau holds an open case. Shown for awareness; no link is suggested.
        {bureau && ` Only those where ${bureau} is one of the bureaus.`}
      </p>
      {error && <p role="alert">{error}</p>}
      {shown && shown.length === 0 && <p>None right now.</p>}
      {shown && shown.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Institution</th>
              <th>Bureaus</th>
              <th>Open cases</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((t) => (
              <tr key={t.institution_id}>
                <td>
                  <a href={`#/institutions/${t.institution_id}`}>{t.institution}</a>
                  {t.tier2_pairs > 0 && (
                    <>
                      <br />
                      <small>also a possible same-matter overlap</small>
                    </>
                  )}
                </td>
                <td>{t.bureaus.join(", ")}</td>
                <td>
                  {t.cases.map((c, n) => (
                    <span key={c.id}>
                      {n > 0 && ", "}
                      <a href={`#/cases/${c.id}`}>{c.ref}</a> ({c.bureau})
                    </span>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
