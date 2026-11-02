export const LEVELS = ["A1-A2", "B1-B2", "C1-C2"] as const;
export type User = {
  id: string;
  name: string;
  email: string;
  role: "student" | "admin";
  active: boolean;
  group_id: number | null;
  group_name: string | null;
  blocked_levels: string[];
  personal_blocks: string[];
  listens?: number;
  recordings?: number;
};
export type Material = {
  id: string;
  title: string;
  description: string;
  status: string;
  version_id: string;
  number: number;
  level: string;
  duration: number;
  count: number;
  script?: string;
  audio_url?: string;
};
export type Review = {
  score: number;
  comment: string;
  reviewer: string;
  reviewed_at: string;
  editor: string;
  edited_at: string;
  revision: number;
};
export type Recording = {
  id: string;
  user_id: string;
  user_name: string;
  group_id: number | null;
  title: string;
  material_id: string;
  version_id: string;
  number: number;
  duration: number;
  status: string;
  created_at: string;
  audio_url: string;
  review: Review | null;
};
export type Group = {
  id: number;
  name: string;
  students: number;
  blocked_levels: string[];
};
export const time = (s: number) =>
  `${Math.floor(s / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(s % 60)
    .toString()
    .padStart(2, "0")}`;
export const date = (s: string) =>
  new Intl.DateTimeFormat("uz-UZ", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Tashkent",
  }).format(new Date(s));
export const statusLabel: Record<string, string> = {
  saved: "Yuborilmagan",
  submitted: "Tekshirishda",
  graded: "Baholangan",
  draft: "Qoralama",
  published: "E’lon qilingan",
  archived: "Arxivlangan",
};
