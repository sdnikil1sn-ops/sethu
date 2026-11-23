import { useState } from "react";
import { download, upload } from "../../api";
import { type Attachment, type Case, type Enrichment as E, day, words } from "./types";

// ISO code -> name: the 22 scheduled languages and English (backend/app/ai/lid.py).
export const LANGUAGE: Record<string, string> = {
  as: "Assamese", bn: "Bengali", brx: "Bodo", doi: "Dogri", gu: "Gujarati", hi: "Hindi", kn: "Kannada",
  ks: "Kashmiri", gom: "Konkani", mai: "Maithili", ml: "Malayalam", mni: "Manipuri", mr: "Marathi", ne: "Nepali",
  or: "Odia", pa: "Punjabi", sa: "Sanskrit", sat: "Santali", sd: "Sindhi", ta: "Tamil", te: "Telugu", ur: "Urdu",
  en: "English", unknown: "not recognised",
};

const TRANSLATION: Record<string, string> = {
  model: "Machine translation (IndicTrans2). Check names, numbers and dates against the original.",
  glossary: "Glossary only: no translation could be made. These are the known terms found in the text.",
  untranslated: "Untranslated: no translation could be made with enough confidence. A person has been asked to review it.",
};
const READ_BY: Record<string, string> = {
  embedded: "taken from the PDF's own text",
  primary: "read by OCR (RapidOCR)",
  fallback: "read by OCR (Tesseract, the fallback)",
  manual: "could not be read with enough confidence: needs manual entry",
};

/** The language badge for the original text. */
export function LanguageBadge({ e }: { e: E | null }) {
  if (!e?.language) return null;
  const sure = e.language_confidence === null ? "" : ` (${Math.round(e.language_confidence * 100)}% sure)`;
  return (
    <small className="badge" title="Detected by the AI layer">
      Language: {LANGUAGE[e.language] ?? e.language}
      {sure}
    </small>
  );
}

/** What the AI pipeline found, beside the original (which it never changes). */
export function EnrichmentPanel({ c }: { c: Case }) {
  const e = c.enrichment;
  if (!e) return null;
  if (e.status === "pending")
    return <p className="note">The AI layer has not finished with this case yet. The case can be worked on now.</p>;
  return (
    <>
      {e.translation_path && e.translation_path !== "not_needed" && (
        <>
          <h2>In English</h2>
          <p className="note">{TRANSLATION[e.translation_path]}</p>
          {e.translated_text && (
            <p className="complaint" lang="en">
              {e.translated_text}
            </p>
          )}
        </>
      )}
      {e.tags.length > 0 && (
        <p>
          Terms recognised (glossary v{e.glossary_version}, term normalisation, not translation):{" "}
          {e.tags.map((t) => (
            <span key={t} className="tag">
              {t}
            </span>
          ))}
        </p>
      )}
      {e.ocr_path && (
        <details>
          <summary>Text from the attachments ({READ_BY[e.ocr_path] ?? words(e.ocr_path)})</summary>
          {e.ocr_text ? <p className="complaint">{e.ocr_text}</p> : <p>No text.</p>}
        </details>
      )}
      {e.status === "review" && (
        <p role="note">
          The AI layer was unsure about part of this case; it is listed under <a href="#/review">Review</a>.
        </p>
      )}
    </>
  );
}

const OCR_STATUS: Record<string, string> = {
  pending: "waiting to be read",
  done: "read",
  review: "needs a person to read it",
  skipped: "not read",
};

/** Scans and PDFs: listed for whoever may read the case; added by its holding bureau. */
export function Attachments({ c, onAdded }: { c: Case; onAdded: () => void }) {
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (!c.readable) return null;

  async function add(file: File | undefined) {
    if (!file) return;
    if (file.size > 10_000_000) {
      setMessage("That file is larger than 10 MB.");
      return;
    }
    setBusy(true);
    try {
      await upload<Attachment>(`/cases/${c.id}/attachments`, file);
      setMessage(`Attached ${file.name}. Its text will be read in the background.`);
      onAdded();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "The upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h2>Attachments</h2>
      {c.attachments.length === 0 ? (
        <p>None.</p>
      ) : (
        <ul className="hits">
          {c.attachments.map((a) => (
            <li key={a.id}>
              <button type="button" onClick={() => download(`/cases/${c.id}/attachments/${a.id}`)}
                aria-label={`Download ${a.filename}`}>
                {a.filename}
              </button>{" "}
              <small>
                {Math.ceil(a.size_bytes / 1024)} KB · added {day(a.created_at)} · {OCR_STATUS[a.ocr_status] ?? a.ocr_status}
              </small>
            </li>
          ))}
        </ul>
      )}
      {c.can_act && (
        <label>
          Add a scan or PDF (PDF, PNG or JPEG, up to 10 MB)
          <input type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" disabled={busy}
            onChange={(e) => add(e.target.files?.[0])} />
        </label>
      )}
      {message && <p role="status">{message}</p>}
      <p className="note">Opening an attachment is recorded in the audit log.</p>
    </>
  );
}
