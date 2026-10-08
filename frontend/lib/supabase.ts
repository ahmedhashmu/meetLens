import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabaseReady = Boolean(url && anonKey);

// Env variables na hon to build fail na ho — page par message dikha denge.
export const supabase = createClient(
  url || "https://placeholder.supabase.co",
  anonKey || "placeholder"
);
