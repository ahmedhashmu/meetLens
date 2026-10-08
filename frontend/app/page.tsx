"use client";

import { useEffect, useState } from "react";
import { supabaseReady } from "@/lib/supabase";
import { api, apiReady, type Client, type Dashboard, type SearchHit } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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

  return (
    <main>
      <div className="card">
        <div className="row">
          <div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{clients.length}</div>
            <div className="muted">Clients</div>
          </div>
          <div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.meetings}</div>
            <div className="muted">Meetings</div>
          </div>
          <div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.pending}</div>
            <div className="muted">Pending follow-ups</div>
          </div>
          <div>
            <div style={{ fontSize: 28, fontWeight: 700 }}>{counts.overdue}</div>
            <div className="muted">Overdue</div>
          </div>
        </div>
      </div>

      <h2>New client</h2>
      <form className="card" onSubmit={addClient}>
        <div className="grid2">
          <div>
            <label htmlFor="n">Name *</label>
            <input id="n" value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <label htmlFor="c">Company</label>
            <input id="c" value={company} onChange={(e) => setCompany(e.target.value)} />
          </div>
        </div>
        <label htmlFor="e">Email</label>
        <input id="e" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label htmlFor="notes">Notes</label>
        <textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)}
                  placeholder="Anything worth remembering about this client..." />
        <button disabled={saving || !supabaseReady || !apiReady}>{saving ? "Saving..." : "Add client"}</button>
        {error && <p className="err">{error}</p>}
      </form>

      <h2>Search meetings</h2>
      <form className="card" onSubmit={runSearch}>
        <label htmlFor="s">Keyword</label>
        <div style={{ display: "flex", gap: 10 }}>
          <input id="s" value={search} onChange={(e) => setSearch(e.target.value)}
                 placeholder="e.g. budget, timeline, pricing..." style={{ flex: 1 }} />
          <button disabled={searching} style={{ marginTop: 0 }}>
            {searching ? "Searching..." : "Search"}
          </button>
        </div>
        {searchResults !== null && (
          <div style={{ marginTop: 14 }}>
            {searchResults.length === 0 && <p className="muted">No meetings match "{search}".</p>}
            {searchResults.map((r) => (
              <a key={r.meeting_id} href={`/clients/${r.client_id}`} className="card" style={{ display: "block", color: "inherit" }}>
                <div className="row">
                  <strong>{r.title}</strong>
                  <span className="muted">{r.client_name} · {r.meeting_date}</span>
                </div>
                <p className="muted" style={{ margin: "6px 0 0" }}>
                  <span className="tag">{r.matched_in}</span> {r.snippet}
                </p>
              </a>
            ))}
          </div>
        )}
      </form>

      <h2>Clients</h2>
      {loading && <p className="muted">Loading...</p>}
      {!loading && clients.length === 0 && !error && (
        <p className="muted">No clients yet. Add one above.</p>
      )}
      {clients.map((c) => (
        <a key={c.id} href={`/clients/${c.id}`} className="card" style={{ display: "block", color: "inherit" }}>
          <div style={{ fontWeight: 600 }}>{c.name}</div>
          <div className="muted">
            {c.company || "no company"}
            {c.email ? ` · ${c.email}` : ""}
          </div>
        </a>
      ))}
    </main>
  );
}
