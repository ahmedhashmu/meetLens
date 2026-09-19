"use client";

import { use, useEffect, useState } from "react";
import { analyzeTranscript } from "@/lib/analyze";
import { supabase, supabaseReady, type Client, type FollowUp, type Meeting } from "@/lib/supabase";

export default function ClientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const [client, setClient] = useState<Client | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [title, setTitle] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [transcript, setTranscript] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setError("");
    const [c, m, f] = await Promise.all([
      supabase.from("clients").select("*").eq("id", id).single(),
      supabase.from("meetings").select("*").eq("client_id", id).order("meeting_date", { ascending: false }),
      supabase.from("followups").select("*").eq("client_id", id).order("created_at", { ascending: false }),
    ]);

    if (c.error) setError(c.error.message);
    setClient(c.data ?? null);
    setMeetings(m.data ?? []);
    setFollowups(f.data ?? []);
    setLoading(false);
  }

  useEffect(() => {
    if (!supabaseReady) {
      setLoading(false);
      setError("Supabase env variables set nahi hain.");
      return;
    }
    load();
  }, [id]);

  async function addMeeting(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || transcript.trim().length < 20) {
      setError("Title zaroori hai aur transcript kam se kam 20 characters ka ho.");
      return;
    }

    setSaving(true);
    setError("");

    const result = analyzeTranscript(transcript);

    const { data: meeting, error: mErr } = await supabase
      .from("meetings")
      .insert({
        client_id: id,
        title: title.trim(),
        meeting_date: date,
        transcript: transcript.trim(),
        summary: result.summary,
        topics: result.topics,
        concerns: result.concerns,
      })
      .select()
      .single();

    if (mErr || !meeting) {
      setSaving(false);
      setError(mErr?.message ?? "Meeting save nahi hui.");
      return;
    }

    if (result.followups.length > 0) {
      await supabase.from("followups").insert(
        result.followups.map((body) => ({
          client_id: id,
          meeting_id: meeting.id,
          body,
          status: "pending",
        }))
      );
    }

    setSaving(false);
    setTitle("");
    setTranscript("");
    load();
  }

  async function toggle(f: FollowUp) {
    const next = f.status === "pending" ? "done" : "pending";
    setFollowups((prev) => prev.map((x) => (x.id === f.id ? { ...x, status: next } : x)));
    const { error } = await supabase.from("followups").update({ status: next }).eq("id", f.id);
    if (error) {
      setError(error.message);
      load();
    }
  }

  if (loading) return <p className="muted">Load ho raha hai...</p>;
  if (!client) return <p className="err">{error || "Client nahi mila."} <a href="/">Wapas</a></p>;

  const pending = followups.filter((f) => f.status === "pending");

  return (
    <main>
      <p className="muted"><a href="/">← Saare clients</a></p>

      <div className="card">
        <div style={{ fontSize: 20, fontWeight: 700 }}>{client.name}</div>
        <div className="muted">
          {client.company || "company nahi di"}
          {client.email ? ` · ${client.email}` : ""}
        </div>
        <div className="muted" style={{ marginTop: 8 }}>
          {meetings.length} meetings · {pending.length} pending follow-ups
        </div>
      </div>

      <h2>Nayi meeting — transcript paste karein</h2>
      <form className="card" onSubmit={addMeeting}>
        <div className="grid2">
          <div>
            <label htmlFor="t">Title *</label>
            <input id="t" value={title} onChange={(e) => setTitle(e.target.value)}
                   placeholder="Q3 review call" required />
          </div>
          <div>
            <label htmlFor="d">Tareekh</label>
            <input id="d" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </div>
        <label htmlFor="tr">Transcript *</label>
        <textarea id="tr" value={transcript} onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Meeting ki baat cheet yahan paste karein..." required />
        <button disabled={saving}>{saving ? "Analyse ho raha..." : "Save + analyse karein"}</button>
        {error && <p className="err">{error}</p>}
        <p className="muted" style={{ marginTop: 10 }}>
          Abhi analysis local keyword-based hai (demo). Asli OpenAI analysis backend mein likhi hui hai.
        </p>
      </form>

      <h2>Follow-up items</h2>
      <div className="card">
        {followups.length === 0 && <p className="muted">Abhi koi follow-up nahi.</p>}
        {followups.map((f) => (
          <div key={f.id} className={`fu ${f.status === "done" ? "done" : ""}`}>
            <input type="checkbox" checked={f.status === "done"} onChange={() => toggle(f)} />
            <span className="body">
              {f.body}
              {f.due_date && <span className="muted"> · due {f.due_date}</span>}
            </span>
          </div>
        ))}
      </div>

      <h2>Timeline</h2>
      {meetings.length === 0 && <p className="muted">Abhi koi meeting nahi.</p>}
      {meetings.map((m) => (
        <div key={m.id} className="card">
          <div className="row">
            <strong>{m.title}</strong>
            <span className="muted">{m.meeting_date}</span>
          </div>
          {m.summary && <p style={{ marginBottom: 10 }}>{m.summary}</p>}
          {m.topics?.length > 0 && (
            <div>{m.topics.map((t) => <span key={t} className="tag">{t}</span>)}</div>
          )}
          {m.concerns?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div className="muted" style={{ marginBottom: 4 }}>Concerns:</div>
              {m.concerns.map((c, i) => <span key={i} className="tag warn">{c}</span>)}
            </div>
          )}
        </div>
      ))}
    </main>
  );
}
