"use client";

import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";

export default function AccountBadge() {
  const { user, loading } = useAuth();

  if (loading || !user) return null;

  return (
    <div className="row" style={{ alignItems: "center", gap: 10 }}>
      <span className="muted">{user.email}</span>
      <button
        type="button"
        className="ghost"
        style={{ marginTop: 0 }}
        onClick={() => supabase.auth.signOut()}
      >
        Log out
      </button>
    </div>
  );
}
