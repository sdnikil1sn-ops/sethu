import { useState } from "react";
import { useLoad } from "../../api";
import { accessToken } from "../../auth";

type Term = { language: string; term: string; english: string; type: string; notes: string | null; needs_review: boolean };
type Glossary = { version: number; terms: Term[]; versions: { version: number; terms: number; created_at: string }[] };
type RowError = { row: number; field: string; problem: string };

/** Admin > Glossary: term normalisation for complaints, NOT translation. A whole new list is uploaded; it is taken
 *  only if every row passes, otherwise the error report says which row and field. */
export function GlossaryAdmin() {
  const { data, error, reload } = useLoad<Glossary>("/glossary");
  const [message, setMessage] = useState<string | null>(null);
  const [problems, setProblems] = useState<RowError[]>([]);

  async function send(file: File | undefined) {
    if (!file) return;
    setProblems([]);
    const response = await fetch(`/api/v1/admin/glossary?filename=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${await accessToken()}`, "Content-Type": "application/octet-stream" },
      body: file,
    });
    const body = await response.json().catch(() => ({}));
    if (response.ok) {
      setMessage(`Version ${body.version} is in use: ${body.terms} terms. Recorded in the audit log.`);
      reload();
    } else if (body.detail?.errors) {
      setMessage(`${body.detail.message}. Nothing was stored; fix these rows and upload the whole file again.`);
      setProblems(body.detail.errors);
    } else {
      setMessage(typeof body.detail === "string" ? body.detail : `The upload failed (${response.status}).`);
    }
  }

  const review = data?.terms.filter((t) => t.needs_review).length ?? 0;
  return (
    <>
      <h2>Glossary (term normalisation, not translation)</h2>
      <p className="note">
        Known terms in Indian languages and spellings, each with an English tag (for example छात्रवृत्ति → scholarship).
        The AI layer tags complaints with them. It does not translate. Upload the whole list as CSV or XLSX with the
        columns language, term, english, type, notes, needs_review; the starter list is seed/glossary.csv.
      </p>
      {error && <p role="alert">{error}</p>}
      {data && (
        <p>
          Version {data.version} in use: {data.terms.length} terms in{" "}
          {[...new Set(data.terms.map((t) => t.language))].sort().join(", ") || "no language"}.
          {review > 0 && <> {review} marked “needs native review”.</>}
        </p>
      )}
      <label>
        Upload a new version
        <input type="file" accept=".csv,.xlsx" onChange={(e) => send(e.target.files?.[0])} />
      </label>
      {message && <p role="status">{message}</p>}
      {problems.length > 0 && (
        <table>
          <caption>Error report</caption>
          <thead>
            <tr>
              <th scope="col">Row</th>
              <th scope="col">Field</th>
              <th scope="col">Problem</th>
            </tr>
          </thead>
          <tbody>
            {problems.slice(0, 200).map((p) => (
              <tr key={`${p.row}-${p.field}`}>
                <td>{p.row}</td>
                <td>{p.field}</td>
                <td>{p.problem}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
