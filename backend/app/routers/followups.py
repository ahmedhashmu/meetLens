"""Follow-up tracker aur email reminders."""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, owned_client
from app.models import Client, FollowUp, User
from app.schemas import FollowUpIn, FollowUpOut, FollowUpUpdate, ReminderResult
from app.services.email_service import send_reminders

router = APIRouter(prefix="/followups", tags=["followups"])


def _owned(followup_id: str, db: Session, user: User) -> FollowUp:
    followup = db.get(FollowUp, followup_id)
    if followup is None or followup.client.user_id != user.id:
        raise HTTPException(status_code=404, detail="Follow-up nahi mila.")
    return followup


@router.post("", response_model=FollowUpOut, status_code=201)
def create_followup(payload: FollowUpIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owned_client(payload.client_id, db, user)
    followup = FollowUp(**payload.model_dump())
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup


@router.get("", response_model=list[FollowUpOut])
def list_followups(
    client_id: str | None = None,
    status: str | None = Query(default=None, pattern="^(pending|done)$"),
    overdue: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(FollowUp).join(Client).filter(Client.user_id == user.id)

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
    followup_id: str,
    payload: FollowUpUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    followup = _owned(followup_id, db, user)
    changes = payload.model_dump(exclude_unset=True)

    if "status" in changes:
        followup.completed_at = datetime.now(timezone.utc) if changes["status"] == "done" else None

    for field, value in changes.items():
        setattr(followup, field, value)

    db.commit()
    db.refresh(followup)
    return followup


@router.delete("/{followup_id}", status_code=204)
def delete_followup(followup_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.delete(_owned(followup_id, db, user))
    db.commit()


@router.post("/remind", response_model=ReminderResult)
def remind(
    within_days: int = Query(default=3, ge=0, le=60),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Due/overdue follow-ups ki reminder email bhejta hai."""
    sent, skipped, detail = send_reminders(db, user, within_days)
    return ReminderResult(sent=sent, skipped=skipped, detail=detail)
