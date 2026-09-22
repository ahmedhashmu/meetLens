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

  const [fuBody, setFuBody] = useState("");
  const [fuOwner, setFuOwner] = useState("");
  const [fuDue, setFuDue] = useState("");
  const [fuSaving, setFuSaving] = useState(false);

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
      setError("Supabase env variables are not set.");
      return;
    }
    load();
  }, [id]);

  async function addMeeting(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || transcript.trim().length < 20) {
      setError("Title is required and transcript must be at least 20 characters.");
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
      setError(mErr?.message ?? "Failed to save meeting.");
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

  async function setStatus(f: FollowUp, next: FollowUp["status"]) {
    setFollowups((prev) => prev.map((x) => (x.id === f.id ? { ...x, status: next } : x)));
    const { error } = await supabase.from("followups").update({ status: next }).eq("id", f.id);
    if (error) {
      setError(error.message);
      load();
    }
  }

  async function addFollowup(e: React.FormEvent) {
    e.preventDefault();
    if (!fuBody.trim()) return;
    setFuSaving(true);
    setError("");

    const { error } = await supabase.from("followups").insert({
      client_id: id,
      body: fuBody.trim(),
      owner: fuOwner.trim() || null,
      due_date: fuDue || null,
      status: "pending",
    });

    setFuSaving(false);
    if (error) {
      setError(error.message);
      return;
    }
    setFuBody("");
    setFuOwner("");
    setFuDue("");
    load();
  }

  if (loading) return <p className="muted">Loading...</p>;
  if (!client) return <p className="err">{error || "Client not found."} <a href="/">Back</a></p>;

  const pending = followups.filter((f) => f.status === "pending");

  return (
    <main>
      <p className="muted"><a href="/">← All clients</a></p>

      <div className="card">
        <div style={{ fontSize: 20, fontWeight: 700 }}>{client.name}</div>
        <div className="muted">
          {client.company || "no company"}
          {client.email ? ` · ${client.email}` : ""}
        </div>
        <div className="muted" style={{ marginTop: 8 }}>
          {meetings.length} meetings · {pending.length} pending follow-ups
        </div>
        {client.notes && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border)" }}>
            {client.notes}
          </div>
        )}
      </div>

      <h2>New meeting — paste transcript</h2>
      <form className="card" onSubmit={addMeeting}>
        <div className="grid2">
          <div>
            <label htmlFor="t">Title *</label>
            <input id="t" value={title} onChange={(e) => setTitle(e.target.value)}
                   placeholder="Q3 review call" required />
          </div>
          <div>
            <label htmlFor="d">Date</label>
            <input id="d" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
        </div>
        <label htmlFor="tr">Transcript *</label>
        <textarea id="tr" value={transcript} onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Paste the meeting conversation here..." required />
        <button disabled={saving}>{saving ? "Analysing..." : "Save + analyse"}</button>
        {error && <p className="err">{error}</p>}
        <p className="muted" style={{ marginTop: 10 }}>
          Analysis is currently local keyword-based (demo). The real OpenAI analysis is written in the backend.
        </p>
      </form>

      <h2>Follow-up items</h2>
      <form className="card" onSubmit={addFollowup}>
        <label htmlFor="fb">New follow-up</label>
        <input id="fb" value={fuBody} onChange={(e) => setFuBody(e.target.value)}
               placeholder="e.g. Send updated proposal" required />
        <div className="grid2">
          <div>
            <label htmlFor="fo">Owner</label>
            <input id="fo" value={fuOwner} onChange={(e) => setFuOwner(e.target.value)} placeholder="Who's responsible" />
          </div>
          <div>
            <label htmlFor="fd">Due date</label>
            <input id="fd" type="date" value={fuDue} onChange={(e) => setFuDue(e.target.value)} />
          </div>
        </div>
        <button disabled={fuSaving}>{fuSaving ? "Adding..." : "Add follow-up"}</button>
      </form>

      <div className="card">
        {followups.length === 0 && <p className="muted">No follow-ups yet.</p>}
        {followups.map((f) => (
          <div key={f.id} className={`fu ${f.status !== "pending" ? "done" : ""}`}>
            <select
              value={f.status}
              onChange={(e) => setStatus(f, e.target.value as FollowUp["status"])}
              style={{ width: "auto", padding: "4px 8px", fontSize: 12 }}
            >
              <option value="pending">Pending</option>
              <option value="done">Done</option>
              <option value="dropped">Dropped</option>
            </select>
            <span className="body">
              {f.body}
              {f.owner && <span className="muted"> · {f.owner}</span>}
              {f.due_date && <span className="muted"> · due {f.due_date}</span>}
            </span>
          </div>
        ))}
      </div>

      <h2>Timeline</h2>
      {meetings.length === 0 && <p className="muted">No meetings yet.</p>}
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
