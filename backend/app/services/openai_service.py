"""Transcript se summary, topics, concerns aur follow-ups nikalta hai."""
import json
import logging
from dataclasses import dataclass, field

from fastapi import HTTPException

from app.config import settings

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


def analyse_transcript(transcript: str, retries: int = 2) -> AnalysisResult:
    """OpenAI ko call karke structured analysis wapas karta hai."""
    if not settings.ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY set nahi hai, is liye analysis nahi ho sakti.",
        )

    from openai import OpenAI, OpenAIError

    text = transcript.strip()[:MAX_TRANSCRIPT_CHARS]
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    last_error: Exception | None = None

    for attempt in range(1, retries + 2):
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                temperature=0.2,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Meeting transcript:\n\n{text}"},
                ],
            )
            return _parse(response.choices[0].message.content or "", settings.OPENAI_MODEL)
        except (OpenAIError, ValueError) as exc:
            last_error = exc
            logger.warning("Analysis attempt %s failed: %s", attempt, exc)

    raise HTTPException(status_code=502, detail=f"AI analysis fail ho gayi: {last_error}")
