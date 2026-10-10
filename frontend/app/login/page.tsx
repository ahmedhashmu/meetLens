"use client";

import { useState } from "react";
import { supabase, supabaseReady } from "@/lib/supabase";
import { Brand } from "../Shell";

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
      setNotice("Account created. Check your email to confirm it, then sign in.");
      setMode("signin");
    }
  }

  function switchTo(next: "signin" | "signup") {
    setError("");
    setNotice("");
    setMode(next);
  }

  return (
    <div className="auth">
      <section className="auth-side">
        <div>
          <Brand />
          <h1>Never forget what you promised a client.</h1>
          <p className="lead">
            Paste a meeting transcript or upload the recording. MeetLens writes the summary,
            flags the concerns and keeps track of every follow-up.
          </p>

          <div className="sample" aria-hidden>
            <div className="when">BrightPath Logistics · 14 Oct</div>
            <h3>Kickoff call</h3>
            <p>Client wants the tracking dashboard live before the end of November. Main worries are duplicate warehouse data and the budget for mobile.</p>
            <div className="fu">
              <input type="checkbox" readOnly />
              <div className="body">
                <div className="text">Send revised quote with web and mobile split</div>
                <div className="meta">Ahmed · due 17 Oct</div>
              </div>
            </div>
            <div className="fu">
              <input type="checkbox" readOnly />
              <div className="body">
                <div className="text">Share cleanup script with their IT lead</div>
                <div className="meta">Ahmed · due 20 Oct</div>
              </div>
            </div>
          </div>
        </div>
        <div className="credit">Software Project Management · UBIT</div>
      </section>

      <main className="auth-main">
        <form className="auth-card" onSubmit={submit}>
          <h2>{mode === "signin" ? "Welcome back" : "Create your account"}</h2>
          <p className="sub">
            {mode === "signin" ? "Sign in to see your clients and follow-ups." : "It takes less than a minute."}
          </p>

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
            autoFocus
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={mode === "signup" ? "At least 6 characters" : ""}
            minLength={6}
            required
          />

          <button type="submit" disabled={loading || !supabaseReady}>
            {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>

          {!supabaseReady && <p className="err">Supabase env variables are not set.</p>}
          {error && <p className="err">{error}</p>}
          {notice && <p className="note">{notice}</p>}

          <p className="auth-switch">
            {mode === "signin" ? (
              <>New here? <a href="#" onClick={(e) => { e.preventDefault(); switchTo("signup"); }}>Create an account</a></>
            ) : (
              <>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); switchTo("signin"); }}>Sign in</a></>
            )}
          </p>
        </form>
      </main>
    </div>
  );
}
