"use client";

import { use, useEffect, useState } from "react";
import { supabaseReady } from "@/lib/supabase";
import { api, apiReady, type ClientDetail, type FollowUp, type Meeting } from "@/lib/api";

export default function ClientPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const [client, setClient] = useState<ClientDetail | null>(null);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [followups, setFollowups] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [mode, setMode] = useState<"paste" | "audio">("paste");
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [transcript, setTranscript] = useState("");
  const [audio, setAudio] = useState<File | null>(null);
  const [saving, setSaving] = useState("");
  const [analysing, setAnalysing] = useState<string | null>(null);

  const [fuBody, setFuBody] = useState("");
  const [fuOwner, setFuOwner] = useState("");
  const [fuDue, setFuDue] = useState("");
  const [fuSaving, setFuSaving] = useState(false);

  async function load() {
    setError("");
    try {
      const [c, m, f] = await Promise.all([
        api<ClientDetail>(`/clients/${id}`),
        api<Meeting[]>(`/meetings?client_id=${id}`),
        api<FollowUp[]>(`/followups?client_id=${id}`),
      ]);
      setClient(c);
      setMeetings(m);
      setFollowups(f);
    } catch (err) {
      setError((err as Error).message);
    }
    setLoading(false);
  }

  useEffect(() => {
    if (!supabaseReady || !apiReady) {
      setLoading(false);
      setError(!supabaseReady ? "Supabase env variables are not set." : "Backend URL is not set (NEXT_PUBLIC_API_URL).");
      return;
    }
    load();
  }, [id]);

  async function analyse(meetingId: string) {
    await api(`/meetings/${meetingId}/analyze`, { method: "POST" });
  }

  async function addMeeting(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Title is required.");
      return;
    }
    if (mode === "paste" && transcript.trim().length < 20) {
      setError("Transcript must be at least 20 characters.");
      return;
    }
    if (mode === "audio" && !audio) {
      setError("Choose an audio file.");
      return;
    }

    setError("");
    let meeting: Meeting;
    try {
      if (mode === "paste") {
        setSaving("Saving...");
        meeting = await api<Meeting>("/meetings", {
          method: "POST",
          body: JSON.stringify({
            client_id: id,
            title: title.trim(),
            meeting_date: date,
            transcript: transcript.trim(),
          }),
        });
      } else {
        setSaving("Transcribing audio...");
        const form = new FormData();
        form.append("client_id", id);
        form.append("title", title.trim());
        form.append("meeting_date", date);
        form.append("audio", audio as File);
        meeting = await api<Meeting>("/meetings/upload", { method: "POST", body: form });
      }
    } catch (err) {
      setSaving("");
      setError((err as Error).message);
      return;
    }

    setSaving("Analysing with AI...");
    try {
      await analyse(meeting.id);
    } catch (err) {
      setError(`Meeting saved, but analysis failed: ${(err as Error).message}`);
    }

    setSaving("");
    setTitle("");
    setTranscript("");
    setAudio(null);
    load();
  }

  async function reanalyse(meetingId: string) {
    setAnalysing(meetingId);
    setError("");
    try {
      await analyse(meetingId);
    } catch (err) {
      setError((err as Error).message);
    }
    setAnalysing(null);
    load();
  }

  async function setStatus(f: FollowUp, next: FollowUp["status"]) {
    setFollowups((prev) => prev.map((x) => (x.id === f.id ? { ...x, status: next } : x)));
    try {
      await api(`/followups/${f.id}`, { method: "PATCH", body: JSON.stringify({ status: next }) });
    } catch (err) {
      setError((err as Error).message);
      load();
    }
  }

  async function addFollowup(e: React.FormEvent) {
    e.preventDefault();
    if (!fuBody.trim()) return;
    setFuSaving(true);
    setError("");

    try {
      await api<FollowUp>("/followups", {
        method: "POST",
        body: JSON.stringify({
          client_id: id,
          body: fuBody.trim(),
          owner: fuOwner.trim() || null,
          due_date: fuDue || null,
        }),
      });
    } catch (err) {
      setFuSaving(false);
      setError((err as Error).message);
      return;
    }

    setFuSaving(false);
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

      <h2>New meeting</h2>
      <form className="card" onSubmit={addMeeting}>
        <div style={{ display: "flex", gap: 10, marginBottom: 6 }}>
          <button type="button" className={mode === "paste" ? "" : "ghost"} style={{ marginTop: 0 }}
                  onClick={() => setMode("paste")}>
            Paste transcript
          </button>
          <button type="button" className={mode === "audio" ? "" : "ghost"} style={{ marginTop: 0 }}
                  onClick={() => setMode("audio")}>
            Upload recording
          </button>
        </div>
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
        {mode === "paste" ? (
          <>
            <label htmlFor="tr">Transcript *</label>
            <textarea id="tr" value={transcript} onChange={(e) => setTranscript(e.target.value)}
                      placeholder="Paste the meeting conversation here..." required />
          </>
        ) : (
          <>
            <label htmlFor="au">Recording * (mp3, m4a, wav, webm, mp4 — max 25 MB)</label>
            <input id="au" type="file" accept=".mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm,audio/*"
                   onChange={(e) => setAudio(e.target.files?.[0] ?? null)} />
          </>
        )}
        <button disabled={Boolean(saving)}>{saving || "Save + analyse"}</button>
        {error && <p className="err">{error}</p>}
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
              {f.source === "ai" && <span className="tag">AI</span>}
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
            <span className="muted">
              {m.meeting_date}
              {m.source === "audio" ? " · from recording" : ""}
            </span>
          </div>
          {m.summary ? (
            <p style={{ marginBottom: 10 }}>{m.summary}</p>
          ) : (
            <p className="muted">Not analysed yet.</p>
          )}
          {m.topics?.length > 0 && (
            <div>{m.topics.map((t) => <span key={t} className="tag">{t}</span>)}</div>
          )}
          {m.concerns?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div className="muted" style={{ marginBottom: 4 }}>Concerns:</div>
              {m.concerns.map((c, i) => <span key={i} className="tag warn">{c}</span>)}
            </div>
          )}
          <button type="button" className="ghost" disabled={analysing === m.id}
                  onClick={() => reanalyse(m.id)}>
            {analysing === m.id ? "Analysing..." : m.summary ? "Re-analyse" : "Analyse"}
          </button>
        </div>
      ))}
    </main>
  );
}
