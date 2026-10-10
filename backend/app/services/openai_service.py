"""Transcript se summary, topics, concerns aur follow-ups nikalta hai."""
import json
import logging
from dataclasses import dataclass, field

from fastapi import HTTPException


logger = logging.getLogger(__name__)

MAX_TRANSCRIPT_CHARS = 48_000

SYSTEM_PROMPT = """You analyse business meeting transcripts for a consulting firm.
Return ONLY valid JSON with exactly these keys:
  "summary"   : string  - 3 to 5 sentence plain-English summary
  "topics"    : array of short strings - main subjects discussed
  "concerns"  : array of short strings - client worries, risks or complaints
  "followups" : array of objects, each {"text": string, "owner": string|null, "due_date": "YYYY-MM-DD"|null}
Rules:
- "followups" are concrete promised actions only, not vague intentions.
- Use null for owner/due_date when the transcript does not state them.
- Never invent facts that are not in the transcript.
- Resolve relative dates ("Friday", "October 20th", "today") against the meeting date.
- Return at most 10 topics, 10 concerns and 15 followups."""


@dataclass
class AnalysisResult:
    summary: str
    topics: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    followups: list[dict] = field(default_factory=list)
    model_used: str | None = None


def _clean_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append(item.strip()[:300])
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            out.append(item["text"].strip()[:300])
    return out[:limit]


def _clean_followups(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str):
            item = {"text": item}
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        owner = item.get("owner")
        due = item.get("due_date")
        out.append(
            {
                "text": text.strip()[:1000],
                "owner": owner.strip()[:120] if isinstance(owner, str) and owner.strip() else None,
                "due_date": due if isinstance(due, str) and due.strip() else None,
            }
        )
    return out[:15]


def _parse(raw: str, model: str) -> AnalysisResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI ne valid JSON wapas nahi kiya: {exc}") from exc

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("AI ke jawab mein summary nahi thi.")

    return AnalysisResult(
        summary=summary.strip(),
        topics=_clean_list(data.get("topics"), 10),
        concerns=_clean_list(data.get("concerns"), 10),
        followups=_clean_followups(data.get("followups")),
        model_used=model,
    )


def analyse_transcript(transcript: str, meeting_date=None, retries: int = 2) -> AnalysisResult:
    """AI (Gemini ya OpenAI) ko call karke structured analysis wapas karta hai."""
    from openai import OpenAIError

    from app.services.ai_client import extra_options, get_client

    client, model, provider = get_client()
    text = transcript.strip()[:MAX_TRANSCRIPT_CHARS]
    # Date ke baghair model "October 20th" ka saal khud andaze se rakh deta hai
    when = f"Meeting date: {meeting_date.isoformat()}\n" if meeting_date else ""
    last_error: Exception | None = None

    for attempt in range(1, retries + 2):
        try:
            response = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                temperature=0.2,
                **extra_options(provider),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"{when}Meeting transcript:\n\n{text}"},
                ],
            )
            return _parse(_strip_fences(response.choices[0].message.content or ""), model)
        except (OpenAIError, ValueError) as exc:
            last_error = exc
            logger.warning("Analysis attempt %s failed: %s", attempt, exc)

    raise HTTPException(status_code=502, detail=f"AI analysis fail ho gayi: {last_error}")


def _strip_fences(raw: str) -> str:
    """Kuch models JSON ko ```json ... ``` mein lapet dete hain — wo hata do."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()
