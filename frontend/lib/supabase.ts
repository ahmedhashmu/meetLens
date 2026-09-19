import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabaseReady = Boolean(url && anonKey);

// Env variables na hon to build fail na ho — page par message dikha denge.
export const supabase = createClient(
  url || "https://placeholder.supabase.co",
  anonKey || "placeholder"
);

export type Client = {
  id: string;
  name: string;
  company: string | null;
  email: string | null;
  notes: string | null;
  created_at: string;
};

export type Meeting = {
  id: string;
  client_id: string;
  title: string;
  meeting_date: string;
  transcript: string;
  summary: string | null;
  topics: string[];
  concerns: string[];
  created_at: string;
};

export type FollowUp = {
  id: string;
  client_id: string;
  meeting_id: string | null;
  body: string;
  owner: string | null;
  due_date: string | null;
  status: "pending" | "done";
  created_at: string;
};
