import { useState } from "react";
import { api, useLoad } from "../../api";
import type { Case } from "./types";

// Mirrors backend/app/modules/semantic/schemas.py
type Candidate = { institution_id?: string; name?: string; label?: string; category?: string; score: number; method?: string };
type Suggestion = {
  kind: "category" | "institution";
  suggested: string | null;
  candidates: Candidate[];
  path: "model" | "fallback" | "officer";
  provider: string | null;
  confidence: number | null;
  model_version: string | null;
  status: "suggested" | "auto_linked" | "accepted" | "changed" | "rejected";
};
type Suggestions = { category: Suggestion | null; institution: Suggestion | null; categories: string[] };

const PATH = {
  model: "the AI model (E5)",
  fallback: "the fallback rules (keywords, glossary terms, spelling)",
  officer: "nobody: the AI was not sure enough, so an officer picks",
};
const STATUS = {
  suggested: "waiting for a decision",
  auto_linked: "linked automatically (a clear match)",
  accepted: "accepted",
  changed: "changed by an officer",
  rejected: "rejected: the earlier value was kept",
};
const pct = (x: number | null) => (x === null ? "" : `, ${Math.round(x * 100)}% sure`);

/** The AI's suggested category and institution, how they were made, and Accept / Change for the holding bureau. */
export function AiSuggestions({ c, onDone }: { c: Case; onDone: () => void }) {
  const { data, reload } = useLoad<Suggestions>(`/cases/${c.id}/suggestions`);
  const [choice, setChoice] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  if (!data || (!data.category && !data.institution)) return null;

  async function send(path: string, body: object, done: string) {
    try {
      await api(`/cases/${c.id}/suggestions/${path}`, body);
      setMessage(`${done} Recorded in the audit log.`);
      reload();
      onDone();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "The request failed.");
    }
  }

  const cat = data.category;
  const inst = data.institution;
  const open = (s: Suggestion | null) => s?.status === "suggested" && c.can_act;
  return (
    <section aria-labelledby="ai-suggestions">
      <h2 id="ai-suggestions">AI suggestions</h2>
      <p className="note">Suggestions only: nothing changes until a person accepts or changes it.</p>
      {cat && (
        <div>
          <p>
            Category: {cat.suggested ? <strong>{cat.suggested}</strong> : "no suggestion"} (by {PATH[cat.path]}
            {pct(cat.confidence)}; {STATUS[cat.status]}). Filed as: {c.category ?? "none"}.
          </p>
          {cat.candidates.length > 1 && (
            <p>
              <small>
                Other possibilities: {cat.candidates.slice(1).map((x) => `${x.category} ${Math.round(x.score * 100)}%`).join(", ")}
              </small>
            </p>
          )}
          {open(cat) && (
            <p>
              {cat.suggested && (
                <button type="button" onClick={() => send("category", { category: cat.suggested }, `Category set to ${cat.suggested}.`)}>
                  Accept {cat.suggested}
                </button>
              )}{" "}
              <label>
                Change to
                <select value={choice} onChange={(e) => setChoice(e.target.value)}>
                  <option value="">choose…</option>
                  {data.categories.map((x) => (
                    <option key={x} value={x}>
                      {x}
                    </option>
                  ))}
                </select>
              </label>{" "}
              <button type="button" disabled={!choice} onClick={() => send("category", { category: choice }, `Category set to ${choice}.`)}>
                Change
              </button>
            </p>
          )}
        </div>
      )}
      {inst && (
        <div>
          <p>
            Institution: by {PATH[inst.path]}
            {pct(inst.confidence)}; {STATUS[inst.status]}.
          </p>
          {inst.candidates.length > 0 && (
            <ol>
              {inst.candidates.map((x) => (
                <li key={x.institution_id}>
                  {x.name ?? x.label}{" "}
                  <small>
                    ({x.method === "e5" ? `meaning match ${Math.round(x.score * 100)}%` : `spelling ${Math.round(x.score)}`})
                  </small>{" "}
                  {open(inst) && x.institution_id && (
                    <button type="button" onClick={() => send("institution", { institution_id: x.institution_id }, `Linked to ${x.name ?? x.label}.`)}>
                      {x.institution_id === inst.suggested ? "Accept" : "Choose this one"}
                    </button>
                  )}
                </li>
              ))}
            </ol>
          )}
          {open(inst) && (
            <p>
              <small>
                None of these? Pick from all institutions in the <a href="#/queue">resolution queue</a>.
              </small>
            </p>
          )}
        </div>
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
