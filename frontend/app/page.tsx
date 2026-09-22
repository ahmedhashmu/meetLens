"use client";

import { useEffect, useState } from "react";
import { supabase, supabaseReady, type Client } from "@/lib/supabase";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [counts, setCounts] = useState({ meetings: 0, pending: 0 });
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<
    { id: string; title: string; summary: string | null; client_id: string; client_name: string }[] | null
  >(null);
  const [searching, setSearching] = useState(false);

  async function load() {
    setError("");
    const [c, m, f] = await Promise.all([
      supabase.from("clients").select("*").order("created_at", { ascending: false }),
      supabase.from("meetings").select("id", { count: "exact", head: true }),
      supabase
        .from("followups")
        .select("id", { count: "exact", head: true })
        .eq("status", "pending"),
    ]);

    if (c.error) setError(c.error.message);
    setClients(c.data ?? []);
    setCounts({ meetings: m.count ?? 0, pending: f.count ?? 0 });
    setLoading(false);
  }

  useEffect(() => {
    if (!supabaseReady) {
      setLoading(false);
      setError("Supabase env variables are not set (NEXT_PUBLIC_SUPABASE_URL / _ANON_KEY).");
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

    const { error } = await supabase.from("clients").insert({
      name: name.trim(),
      company: company.trim() || null,
      email: email.trim() || null,
      notes: notes.trim() || null,
      user_id: user.id,
    });

    setSaving(false);
    if (error) {
      setError(error.message);
      return;
    }
    setName("");
    setCompany("");
    setEmail("");
    setNotes("");
    load();
  }

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    const term = search.trim();
    if (!term) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    const { data, error } = await supabase
      .from("meetings")
      .select("id, title, summary, client_id, clients(name)")
      .or(`summary.ilike.%${term}%,transcript.ilike.%${term}%,title.ilike.%${term}%`)
      .order("meeting_date", { ascending: false })
      .limit(20);
    setSearching(false);
    if (error) {
      setError(error.message);
      return;
    }
    setSearchResults(
      (data ?? []).map((m: any) => ({
        id: m.id,
        title: m.title,
        summary: m.summary,
        client_id: m.client_id,
        client_name: m.clients?.name ?? "Unknown client",
      }))
    );
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
        <button disabled={saving || !supabaseReady}>{saving ? "Saving..." : "Add client"}</button>
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
              <a key={r.id} href={`/clients/${r.client_id}`} className="card" style={{ display: "block", color: "inherit" }}>
                <div className="row">
                  <strong>{r.title}</strong>
                  <span className="muted">{r.client_name}</span>
                </div>
                {r.summary && <p className="muted" style={{ margin: "6px 0 0" }}>{r.summary}</p>}
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
