"use client";

import { useEffect, useState } from "react";
import { supabase, supabaseReady, type Client } from "@/lib/supabase";

export default function HomePage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [counts, setCounts] = useState({ meetings: 0, pending: 0 });
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
    load();
  }, []);

  async function addClient(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError("");

    const { error } = await supabase.from("clients").insert({
      name: name.trim(),
      company: company.trim() || null,
      email: email.trim() || null,
    });

    setSaving(false);
    if (error) {
      setError(error.message);
      return;
    }
    setName("");
    setCompany("");
    setEmail("");
    load();
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
        <button disabled={saving || !supabaseReady}>{saving ? "Saving..." : "Add client"}</button>
        {error && <p className="err">{error}</p>}
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
