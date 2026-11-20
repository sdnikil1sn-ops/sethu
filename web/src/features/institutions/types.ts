// Mirrors backend/app/modules/institutions/schemas.py
export type Institution = {
  id: string;
  permanent_id: string | null;
  name: string;
  state: string | null;
  district: string | null;
};

export type InstitutionRow = Institution & {
  complaints: number;
  open: number;
  score: number | null;
  why: string | null;
};

export type Candidate = Institution & { score: number; reason: string };

export type CaseSummary = {
  id: string;
  ref: string;
  bureau: string;
  category: string | null;
  status: string;
  filed_at: string;
  due_at: string | null;
  closed_at: string | null;
};

// Mirrors Dna in backend/app/modules/institutions/schemas.py
export type Dna = {
  category_mix: { category: string; cases: number; share: number }[];
  volume: { total: number; last_12_months: number; per_month: number };
  recurrence: { repeat_cases: number; share: number; categories: string[]; window_days: number };
  disposal: { closed: number; median_days: number | null };
  bureaus: { bureau: string; cases: number }[];
  trend: { recent: number; previous: number; window_days: number; direction: "up" | "down" | "flat" };
};

export type Profile = Institution & {
  aliases: { alias: string; source: string }[];
  bureaus: string[];
  open: number;
  closed: number;
  oldest_open: CaseSummary | null;
  complaints: CaseSummary[];
  dna: Dna;
};

export type QueueItem = {
  id: string;
  ref: string;
  bureau: string;
  institution_name_raw: string;
  filed_at: string;
  candidates: Candidate[];
};

export const place = (i: Institution) => [i.district, i.state].filter(Boolean).join(", ");
export const day = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { dateStyle: "medium" });
export const daysSince = (iso: string) => Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
