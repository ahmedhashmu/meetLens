/**
 * FastAPI backend (Railway) se baat karne ka helper.
 *
 * Login Supabase karta hai; yahan har request ke saath Supabase ka access token
 * `Authorization: Bearer ...` mein bheja jata hai, aur backend use verify karta hai.
 */
import { supabase } from "./supabase";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/+$/, "");
export const apiReady = Boolean(API_URL);

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  // FormData (audio upload) ka Content-Type browser khud lagata hai
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((d: any) => d.msg).join(", ");
    } catch {
      // jawab JSON nahi tha — status wala message hi theek hai
    }
    throw new Error(message);
  }

  return (res.status === 204 ? undefined : await res.json()) as T;
}

export type Client = {
  id: string;
  name: string;
  company: string | null;
  email: string | null;
  notes: string | null;
  created_at: string;
};

export type ClientDetail = Client & {
  meeting_count: number;
  pending_followups: number;
};

export type Meeting = {
  id: string;
  client_id: string;
  title: string;
  meeting_date: string;
  source: "paste" | "audio";
  audio_filename: string | null;
  summary: string | null;
  topics: string[];
  concerns: string[];
  analyzed_at: string | null;
  created_at: string;
};

export type FollowUp = {
  id: string;
  client_id: string;
  meeting_id: string | null;
  body: string;
  owner: string | null;
  due_date: string | null;
  status: "pending" | "done" | "dropped";
  source: "ai" | "manual";
  created_at: string;
  completed_at: string | null;
};

export type Dashboard = {
  total_clients: number;
  total_meetings: number;
  pending_followups: number;
  overdue_followups: number;
  done_followups: number;
};

export type SearchHit = {
  meeting_id: string;
  client_id: string;
  client_name: string;
  title: string;
  meeting_date: string;
  snippet: string;
  matched_in: "title" | "summary" | "transcript";
};
