import type { Page } from "../../Pager";
// Mirrors backend/app/modules/complaints/schemas.py
export type CaseRow = {
  id: string;
  ref: string;
  bureau: string;
  bureau_name: string;
  category: string | null;
  status: string;
  institution_id: string | null;
  institution: string | null;
  state: string | null;
  filed_at: string;
  due_at: string | null;
  closed_at: string | null;
  overdue: boolean;
  days_remaining: number | null;
  readable: boolean;
};

export type CasePage = Page<CaseRow>;

export type Action = {
  id: string;
  ref: string;
  action: string;
  from_bureau: string | null;
  to_bureau: string | null;
  actor: string | null;
  assignee: string | null;
  note: string | null;
  reason?: string | null;
  created_at: string;
  acknowledged_at: string | null;
};

export type Case = CaseRow & {
  body: string | null;
  institution_name_raw: string | null;
  language: string | null;
  source: string | null;
  resolution_state: string | null;
  complainant: { name: string; email: string | null; phone: string | null } | null;
  complainant_withheld: boolean;
  assignee_id: string | null;
  assignee: string | null;
  close_reason: string | null;
  deadline_days: number;
  history: Action[];
  can_act: boolean;
  awaiting_acknowledgement: boolean;
  enrichment: Enrichment | null;
  attachments: Attachment[];
};

// Mirrors backend/app/modules/enrichment/schemas.py
export type Enrichment = {
  status: "pending" | "done" | "review";
  language: string | null;
  language_confidence: number | null;
  language_candidates: string[];
  translated_text: string | null;
  translation_path: "not_needed" | "model" | "glossary" | "untranslated" | null;
  tags: string[];
  glossary_version: number | null;
  glossary_coverage: number | null;
  ocr_text: string | null;
  ocr_path: "embedded" | "primary" | "fallback" | "manual" | null;
  updated_at: string;
};

export type Attachment = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
  ocr_status: string;
  created_at: string;
};

export type Options = {
  bureaus: { id: string; code: string; name: string; active: boolean }[];
  categories: string[];
  states: string[];
  statuses: string[];
};

export type Timeline = { actions: Action[]; hidden_cases: number };

export const words = (s: string) => s.replace(/_/g, " ");
export const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { dateStyle: "medium" });
export const moment = (iso: string) =>
  new Date(iso).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" });

/** The 21-day clock in words. */
export function sla(c: CaseRow): string {
  if (c.status === "closed") return c.closed_at ? `Closed ${day(c.closed_at)}` : "Closed";
  if (c.days_remaining === null) return "No due date";
  if (c.days_remaining < 0) return `Overdue by ${-c.days_remaining} day${c.days_remaining === -1 ? "" : "s"}`;
  return c.days_remaining === 0 ? "Due today" : `${c.days_remaining} day${c.days_remaining === 1 ? "" : "s"} left`;
}

/** One history entry as a sentence. */
export function describe(a: Action): string {
  switch (a.action) {
    case "filed":
      return "Filed";
    case "assigned":
      return `Assigned to ${a.assignee ?? "an officer"}`;
    case "transferred":
      return `Transferred from ${a.from_bureau} to ${a.to_bureau}`;
    case "acknowledged":
      return `Transfer from ${a.from_bureau} acknowledged by ${a.to_bureau}`;
    case "replied":
      return "Reply received";
    case "closed":
      return a.reason ? `Closed: ${CLOSE_REASONS[a.reason] ?? words(a.reason)}` : "Closed";
    case "reopened":
      return "Reopened";
    default:
      return "Note";
  }
}

/** Why a case was closed. Mirrors CLOSE_REASONS in backend/app/modules/complaints/service.py. */
export const CLOSE_REASONS: Record<string, string> = {
  resolved: "Resolved",
  no_action_needed: "No action needed",
  duplicate: "Duplicate of another complaint",
  withdrawn: "Withdrawn by the complainant",
  outside_jurisdiction: "Outside AICTE's jurisdiction",
};
