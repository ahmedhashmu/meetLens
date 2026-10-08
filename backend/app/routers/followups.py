"""Follow-up tracker aur email reminders."""
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, owned_client, owned_followup, owned_meeting, user_uuid
from app.models import Client, FollowUp
from app.schemas import FollowUpIn, FollowUpOut, FollowUpStatus, FollowUpUpdate, ReminderResult
from app.services.email_service import send_reminders
from app.services.security import TokenUser

router = APIRouter(prefix="/followups", tags=["followups"])


@router.post("", response_model=FollowUpOut, status_code=201)
def create_followup(payload: FollowUpIn, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    owned_client(payload.client_id, db, user)
    if payload.meeting_id is not None:
        # Meeting bhi isi user ki aur isi client ki honi chahiye
        meeting = owned_meeting(payload.meeting_id, db, user)
        if meeting.client_id != payload.client_id:
            raise HTTPException(status_code=400, detail="Ye meeting is client ki nahi hai.")

    followup = FollowUp(**payload.model_dump(), source="manual")
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup


@router.get("", response_model=list[FollowUpOut])
def list_followups(
    client_id: UUID | None = None,
    status: FollowUpStatus | None = None,
    overdue: bool = False,
    db: Session = Depends(get_db),
    user: TokenUser = Depends(get_current_user),
):
    query = db.query(FollowUp).join(Client).filter(Client.user_id == user_uuid(user))

    if client_id:
        owned_client(client_id, db, user)
        query = query.filter(FollowUp.client_id == client_id)
    if status:
        query = query.filter(FollowUp.status == status)
    if overdue:
        query = query.filter(
            FollowUp.status == "pending",
            FollowUp.due_date.isnot(None),
            FollowUp.due_date < date.today(),
        )

    return query.order_by(FollowUp.due_date.is_(None), FollowUp.due_date.asc()).all()


@router.patch("/{followup_id}", response_model=FollowUpOut)
def update_followup(
    followup_id: UUID,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    user: TokenUser = Depends(get_current_user),
):
    followup = owned_followup(followup_id, db, user)
    changes = payload.model_dump(exclude_unset=True)

    if "status" in changes:
        followup.completed_at = datetime.now(timezone.utc) if changes["status"] == "done" else None

    for field, value in changes.items():
        setattr(followup, field, value)

    db.commit()
    db.refresh(followup)
    return followup


@router.delete("/{followup_id}", status_code=204)
def delete_followup(followup_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    db.delete(owned_followup(followup_id, db, user))
    db.commit()


@router.post("/remind", response_model=ReminderResult)
def remind(
    within_days: int = Query(default=3, ge=0, le=60),
    db: Session = Depends(get_db),
    user: TokenUser = Depends(get_current_user),
):
    """Due/overdue follow-ups ki reminder email bhejta hai."""
    sent, skipped, detail = send_reminders(db, user, within_days)
    return ReminderResult(sent=sent, skipped=skipped, detail=detail)
