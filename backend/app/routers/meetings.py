"""Meetings — transcript paste, audio upload aur AI analysis."""
from datetime import date as date_type
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, owned_client, owned_meeting
from app.models import FollowUp, Meeting
from app.schemas import AnalysisOut, MeetingDetail, MeetingIn, MeetingOut
from app.services import openai_service, whisper_service
from app.services.security import TokenUser

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _save_analysis(db: Session, meeting: Meeting) -> Meeting:
    """Transcript analyse karke meeting par summary/topics/concerns aur follow-ups save karta hai."""
    result = openai_service.analyse_transcript(meeting.transcript)

    meeting.summary = result.summary
    meeting.topics = result.topics
    meeting.concerns = result.concerns
    meeting.model_used = result.model_used
    meeting.analyzed_at = datetime.now(timezone.utc)

    # Dobara analyze karne par purane AI follow-ups hata do, warna har dafa double ho jate hain.
    # User ke khud likhe (manual) aur complete ho chuke follow-ups ko nahi chherte.
    db.query(FollowUp).filter(
        FollowUp.meeting_id == meeting.id,
        FollowUp.source == "ai",
        FollowUp.status == "pending",
    ).delete(synchronize_session="fetch")

    for item in result.followups:
        due = None
        if item["due_date"]:
            try:
                due = date_type.fromisoformat(item["due_date"])
            except ValueError:
                due = None
        db.add(
            FollowUp(
                client_id=meeting.client_id,
                meeting_id=meeting.id,
                body=item["text"],
                owner=item["owner"],
                due_date=due,
                source="ai",
            )
        )

    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("", response_model=MeetingDetail, status_code=201)
def create_meeting(payload: MeetingIn, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    """Transcript paste karke meeting banata hai."""
    owned_client(payload.client_id, db, user)
    meeting = Meeting(**payload.model_dump(), source="paste")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/upload", response_model=MeetingDetail, status_code=201)
async def upload_audio(
    client_id: UUID = Form(...),
    title: str = Form(...),
    meeting_date: date_type = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: TokenUser = Depends(get_current_user),
):
    """Audio upload karke Whisper se transcript banata hai."""
    owned_client(client_id, db, user)

    content = await audio.read()
    whisper_service.validate_audio(audio.filename, len(content))
    transcript = whisper_service.transcribe(content, audio.filename or "audio.mp3")

    meeting = Meeting(
        client_id=client_id,
        title=title,
        meeting_date=meeting_date,
        source="audio",
        transcript=transcript,
        audio_filename=audio.filename,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/analyze", response_model=AnalysisOut)
def analyze(meeting_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    """Meeting ka transcript AI se analyse karta hai."""
    return _save_analysis(db, owned_meeting(meeting_id, db, user))


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    return owned_meeting(meeting_id, db, user)


@router.get("", response_model=list[MeetingOut])
def list_meetings(client_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    owned_client(client_id, db, user)
    return (
        db.query(Meeting)
        .filter(Meeting.client_id == client_id)
        .order_by(Meeting.meeting_date.desc())
        .all()
    )


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    db.delete(owned_meeting(meeting_id, db, user))
    db.commit()
