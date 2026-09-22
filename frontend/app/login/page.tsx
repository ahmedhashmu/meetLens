"use client";

import { useState } from "react";
import { supabase, supabaseReady } from "@/lib/supabase";

export default function LoginPage() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");

    if (mode === "signin") {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      setLoading(false);
      if (error) setError(error.message);
      return;
    }

    const { data, error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
      return;
    }
    if (!data.session) {
      setNotice("Account created. Check your email to confirm before signing in.");
      setMode("signin");
      return;
    }
  }

  return (
    <main style={{ maxWidth: 380, margin: "80px auto 0" }}>
      <h2 style={{ marginTop: 0 }}>{mode === "signin" ? "Sign in" : "Create an account"}</h2>
      <form className="card" onSubmit={submit}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={6}
          required
        />
        <button disabled={loading || !supabaseReady} style={{ width: "100%" }}>
          {loading ? "Please wait..." : mode === "signin" ? "Sign in" : "Sign up"}
        </button>
        {!supabaseReady && (
          <p className="err">Supabase env variables are not set.</p>
        )}
        {error && <p className="err">{error}</p>}
        {notice && <p className="muted" style={{ marginTop: 10 }}>{notice}</p>}
      </form>
      <p className="muted" style={{ textAlign: "center" }}>
        {mode === "signin" ? (
          <>
            No account?{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setError(""); setNotice(""); setMode("signup"); }}>
              Sign up
            </a>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setError(""); setNotice(""); setMode("signin"); }}>
              Sign in
            </a>
          </>
        )}
      </p>
    </main>
  );
}
