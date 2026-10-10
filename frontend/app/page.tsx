"use client";

import { useEffect, useState } from "react";
import { supabaseReady } from "@/lib/supabase";
import { api, apiReady, type Client, type Dashboard, type SearchHit } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate } from "@/lib/format";

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [counts, setCounts] = useState({ meetings: 0, pending: 0, overdue: 0 });
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<SearchHit[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [showNew, setShowNew] = useState(false);

  async function load() {
    setError("");
    try {
      const [c, d] = await Promise.all([api<Client[]>("/clients"), api<Dashboard>("/dashboard")]);
      setClients(c);
      setCounts({ meetings: d.total_meetings, pending: d.pending_followups, overdue: d.overdue_followups });
    } catch (err) {
      setError((err as Error).message);
    }
    setLoading(false);
  }

  useEffect(() => {
    if (!supabaseReady || !apiReady) {
      setLoading(false);
      setError(
        !supabaseReady
          ? "Supabase env variables are not set (NEXT_PUBLIC_SUPABASE_URL / _ANON_KEY)."
          : "Backend URL is not set (NEXT_PUBLIC_API_URL)."
      );
      return;
    }
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    load();
  }, [authLoading, user]);

  async function addClient(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !user) return;
    setSaving(true);
    setError("");

    try {
      await api<Client>("/clients", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          company: company.trim() || null,
          email: email.trim() || null,
          notes: notes.trim() || null,
        }),
      });
    } catch (err) {
      setSaving(false);
      setError((err as Error).message);
      return;
    }

    setSaving(false);
    setShowNew(false);
    setName("");
    setCompany("");
    setEmail("");
    setNotes("");
    load();
  }

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    const term = search.trim();
    if (term.length < 2) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const data = await api<{ results: SearchHit[] }>(`/search?q=${encodeURIComponent(term)}`);
      setSearchResults(data.results);
    } catch (err) {
      setError((err as Error).message);
    }
    setSearching(false);
  }

  const today = new Date().toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });

  return (
    <main>
      <div className="page-head">
        <div>
          <h1>Your clients</h1>
          <p>{today}</p>
        </div>
        {!showNew && (
          <button type="button" onClick={() => setShowNew(true)} disabled={!supabaseReady || !apiReady}>
            + New client
          </button>
        )}
      </div>

      {showNew && (
        <form className="panel" onSubmit={addClient} style={{ marginBottom: 24 }}>
          <div className="panel-title"><h3>New client</h3></div>
          <div className="grid2">
            <div>
              <label htmlFor="n">Name</label>
              <input id="n" value={name} onChange={(e) => setName(e.target.value)} placeholder="Sarah Khan" required autoFocus />
            </div>
            <div>
              <label htmlFor="c">Company</label>
              <input id="c" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="BrightPath Logistics" />
            </div>
          </div>
          <label htmlFor="e">Email</label>
          <input id="e" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="sarah@brightpath.com" />
          <label htmlFor="notes">Notes</label>
          <textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} style={{ minHeight: 80 }}
                    placeholder="How you met, what they care about, anything worth remembering…" />
          <div className="form-actions">
            <button disabled={saving}>{saving ? "Saving…" : "Save client"}</button>
            <button type="button" className="ghost" onClick={() => setShowNew(false)}>Cancel</button>
          </div>
        </form>
      )}

      {error && <p className="err" style={{ marginBottom: 16 }}>{error}</p>}

      <div className="stats">
        <div className="stat"><div className="num">{clients.length}</div><div className="label">Clients</div></div>
        <div className="stat"><div className="num">{counts.meetings}</div><div className="label">Meetings</div></div>
        <div className="stat"><div className="num">{counts.pending}</div><div className="label">Open follow-ups</div></div>
        <div className={`stat ${counts.overdue > 0 ? "alert" : ""}`}>
          <div className="num">{counts.overdue}</div><div className="label">Overdue</div>
        </div>
      </div>

      <div className="section">
        <form className="search" onSubmit={runSearch}>
          <input value={search} onChange={(e) => setSearch(e.target.value)}
                 placeholder="Search meetings, e.g. “budget”" aria-label="Search meetings" />
        </form>
        {searching && <p className="muted" style={{ marginTop: 12 }}>Searching…</p>}
        {searchResults !== null && !searching && (
          <div className="list" style={{ marginTop: 12 }}>
            {searchResults.length === 0 && <div className="empty">Nothing matches “{search}”.</div>}
            {searchResults.map((r) => (
              <a key={r.meeting_id} href={`/clients/${r.client_id}`} className="list-item">
                <div>
                  <div className="title">{r.title}</div>
                  <div className="sub">{r.client_name} · {formatDate(r.meeting_date)} · found in {r.matched_in}</div>
                  <div style={{ marginTop: 6, fontSize: 14, color: "var(--ink-soft)" }}>{r.snippet}</div>
                </div>
                <span className="chev">›</span>
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="section">
        <div className="section-head">
          <h2>All clients</h2>
        </div>
        <div className="list">
          {loading && <div className="empty">Loading…</div>}
          {!loading && clients.length === 0 && !error && (
            <div className="empty">No clients yet. Add your first one to get started.</div>
          )}
          {clients.map((c) => (
            <a key={c.id} href={`/clients/${c.id}`} className="list-item">
              <div>
                <div className="title">{c.name}</div>
                <div className="sub">
                  {c.company || "No company"}
                  {c.email ? ` · ${c.email}` : ""}
                </div>
              </div>
              <span className="chev">›</span>
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
