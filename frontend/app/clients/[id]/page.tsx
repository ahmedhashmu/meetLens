"use client";

import { use, useEffect, useState } from "react";
import { supabaseReady } from "@/lib/supabase";
import { api, apiReady, type ClientDetail, type FollowUp, type Meeting } from "@/lib/api";
import { formatDate } from "@/lib/format";

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

  if (loading) return <p className="muted">Loading…</p>;
  if (!client) return <p className="err">{error || "Client not found."} <a href="/">Back to clients</a></p>;

  const today = new Date().toISOString().slice(0, 10);
  const open = followups.filter((f) => f.status === "pending");
  const closed = followups.filter((f) => f.status !== "pending");

  function FollowUpRow({ f }: { f: FollowUp }) {
    const late = f.status === "pending" && f.due_date && f.due_date < today;
    return (
      <div className={`fu ${f.status}`}>
        <input
          type="checkbox"
          checked={f.status === "done"}
          onChange={() => setStatus(f, f.status === "done" ? "pending" : "done")}
          aria-label="Mark as done"
        />
        <div className="body">
          <div className="text">
            {f.body}
            {f.source === "ai" && <span className="tag ai">AI</span>}
          </div>
          <div className="meta">
            {f.owner || "No owner"}
            {f.due_date && <> · <span className={late ? "overdue" : ""}>{late ? "overdue since " : "due "}{formatDate(f.due_date)}</span></>}
            {" · "}
            <button type="button" className="link" style={{ fontSize: 12.5 }}
                    onClick={() => setStatus(f, f.status === "dropped" ? "pending" : "dropped")}>
              {f.status === "dropped" ? "restore" : "drop"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <main>
      <p style={{ margin: "0 0 14px" }}><a href="/">← All clients</a></p>

      <div className="page-head">
        <div>
          <h1>{client.name}</h1>
          <p>
            {client.company || "No company"}
            {client.email ? <> · <a href={`mailto:${client.email}`}>{client.email}</a></> : ""}
            {" · "}{meetings.length} {meetings.length === 1 ? "meeting" : "meetings"}
          </p>
        </div>
      </div>

      {client.notes && (
        <div className="panel" style={{ marginBottom: 24, background: "var(--paper)" }}>
          <div className="muted" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em" }}>Notes</div>
          <div style={{ marginTop: 4, whiteSpace: "pre-wrap" }}>{client.notes}</div>
        </div>
      )}

      {error && <p className="err" style={{ marginBottom: 16 }}>{error}</p>}

      <div className="client-layout">
        <div>
          <form className="panel" onSubmit={addMeeting}>
            <div className="panel-title"><h3>Add a meeting</h3></div>
            <div className="tabs">
              <button type="button" className={mode === "paste" ? "on" : ""} onClick={() => setMode("paste")}>Paste transcript</button>
              <button type="button" className={mode === "audio" ? "on" : ""} onClick={() => setMode("audio")}>Upload recording</button>
            </div>
            <div className="grid2">
              <div>
                <label htmlFor="t">Title</label>
                <input id="t" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Quarterly review" required />
              </div>
              <div>
                <label htmlFor="d">Date</label>
                <input id="d" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
              </div>
            </div>
            {mode === "paste" ? (
              <>
                <label htmlFor="tr">Transcript</label>
                <textarea id="tr" value={transcript} onChange={(e) => setTranscript(e.target.value)}
                          placeholder="Paste the conversation here…" required />
              </>
            ) : (
              <>
                <label htmlFor="au">Recording</label>
                <input id="au" type="file" accept=".mp3,.mp4,.mpeg,.mpga,.m4a,.wav,.webm,audio/*"
                       onChange={(e) => setAudio(e.target.files?.[0] ?? null)} />
                <p className="note" style={{ marginTop: 6, fontSize: 13 }}>mp3, m4a, wav, webm or mp4 · up to 25 MB</p>
              </>
            )}
            <div className="form-actions">
              <button disabled={Boolean(saving)}>{saving || "Save and analyse"}</button>
            </div>
          </form>

          <div className="panel">
            <div className="panel-title">
              <h3>Meetings</h3>
              <span className="count">newest first</span>
            </div>
            {meetings.length === 0 && <div className="empty" style={{ padding: "12px 0" }}>No meetings yet.</div>}
            {meetings.map((m) => (
              <article key={m.id} className="meeting">
                <div className="row" style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <div>
                    <h3>{m.title}</h3>
                    <div className="meeting-meta">
                      {formatDate(m.meeting_date)}{m.source === "audio" ? " · from a recording" : ""}
                    </div>
                  </div>
                  <button type="button" className="ghost small" disabled={analysing === m.id}
                          onClick={() => reanalyse(m.id)}>
                    {analysing === m.id ? "Analysing…" : m.summary ? "Re-analyse" : "Analyse"}
                  </button>
                </div>
                {m.summary ? <p>{m.summary}</p> : <p className="muted">Not analysed yet.</p>}
                {m.topics?.length > 0 && (
                  <div>{m.topics.map((t) => <span key={t} className="tag">{t}</span>)}</div>
                )}
                {m.concerns?.length > 0 && (
                  <>
                    <div className="label-sm">Concerns</div>
                    <div>{m.concerns.map((c, i) => <span key={i} className="tag warn">{c}</span>)}</div>
                  </>
                )}
              </article>
            ))}
          </div>
        </div>

        <aside>
          <div className="panel">
            <div className="panel-title">
              <h3>Follow-ups</h3>
              <span className="count">{open.length} open</span>
            </div>
            {followups.length === 0 && <p className="muted" style={{ margin: 0 }}>Nothing to follow up on yet.</p>}
            {open.map((f) => <FollowUpRow key={f.id} f={f} />)}
            {closed.length > 0 && (
              <details style={{ marginTop: 10 }}>
                <summary className="muted" style={{ cursor: "pointer" }}>{closed.length} done or dropped</summary>
                {closed.map((f) => <FollowUpRow key={f.id} f={f} />)}
              </details>
            )}

            <form onSubmit={addFollowup} style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid var(--line)" }}>
              <label htmlFor="fb">Add a follow-up</label>
              <input id="fb" value={fuBody} onChange={(e) => setFuBody(e.target.value)} placeholder="Send the updated proposal" required />
              <div className="grid2">
                <div>
                  <label htmlFor="fo">Owner</label>
                  <input id="fo" value={fuOwner} onChange={(e) => setFuOwner(e.target.value)} placeholder="Who" />
                </div>
                <div>
                  <label htmlFor="fd">Due</label>
                  <input id="fd" type="date" value={fuDue} onChange={(e) => setFuDue(e.target.value)} />
                </div>
              </div>
              <div className="form-actions">
                <button className="ghost" disabled={fuSaving}>{fuSaving ? "Adding…" : "Add"}</button>
              </div>
            </form>
          </div>
        </aside>
      </div>
    </main>
  );
}
