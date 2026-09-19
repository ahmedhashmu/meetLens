"""Dashboard counts aur keyword search."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Analysis, Client, FollowUp, Meeting, User
from app.schemas import DashboardOut, FollowUpOut, MeetingOut, SearchHit, SearchOut

router = APIRouter(tags=["dashboard"])

SNIPPET_PAD = 90


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    clients = db.query(Client).filter(Client.user_id == user.id)
    meetings = db.query(Meeting).join(Client).filter(Client.user_id == user.id)
    followups = db.query(FollowUp).join(Client).filter(Client.user_id == user.id)

    return DashboardOut(
        total_clients=clients.count(),
        total_meetings=meetings.count(),
        pending_followups=followups.filter(FollowUp.status == "pending").count(),
        overdue_followups=followups.filter(
            FollowUp.status == "pending",
            FollowUp.due_date.isnot(None),
            FollowUp.due_date < date.today(),
        ).count(),
        done_followups=followups.filter(FollowUp.status == "done").count(),
        recent_meetings=[
            MeetingOut.model_validate(m)
            for m in meetings.order_by(Meeting.created_at.desc()).limit(5)
        ],
        upcoming_followups=[
            FollowUpOut.model_validate(f)
            for f in followups.filter(FollowUp.status == "pending")
            .order_by(FollowUp.due_date.is_(None), FollowUp.due_date.asc())
            .limit(5)
        ],
    )


def _snippet(text: str, needle: str) -> str:
    position = text.lower().find(needle.lower())
    if position < 0:
        return text[: SNIPPET_PAD * 2].strip()
    start = max(0, position - SNIPPET_PAD)
    end = min(len(text), position + len(needle) + SNIPPET_PAD)
    return ("..." if start else "") + text[start:end].strip() + ("..." if end < len(text) else "")


@router.get("/search", response_model=SearchOut)
def search(
    q: str = Query(min_length=2, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Transcripts aur summaries mein keyword dhoondta hai."""
    pattern = f"%{q}%"
    rows = (
        db.query(Meeting, Client, Analysis)
        .join(Client, Meeting.client_id == Client.id)
        .outerjoin(Analysis, Analysis.meeting_id == Meeting.id)
        .filter(
            Client.user_id == user.id,
            or_(
                Meeting.transcript.ilike(pattern),
                Meeting.title.ilike(pattern),
                Analysis.summary.ilike(pattern),
            ),
        )
        .order_by(Meeting.meeting_date.desc())
        .limit(30)
        .all()
    )

    results = []
    for meeting, client, analysis in rows:
        low = q.lower()
        if low in meeting.title.lower():
            where, source = "title", meeting.title
        elif analysis and analysis.summary and low in analysis.summary.lower():
            where, source = "summary", analysis.summary
        else:
            where, source = "transcript", meeting.transcript

        results.append(
            SearchHit(
                meeting_id=meeting.id,
                client_id=client.id,
                client_name=client.name,
                title=meeting.title,
                meeting_date=meeting.meeting_date,
                snippet=_snippet(source, q),
                matched_in=where,
            )
        )

    return SearchOut(query=q, count=len(results), results=results)
