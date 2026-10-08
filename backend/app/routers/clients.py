"""Clients CRUD aur timeline."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, owned_client, user_uuid
from app.models import Client, FollowUp, Meeting
from app.schemas import ClientDetail, ClientIn, ClientOut, ClientUpdate, TimelineItem
from app.services.security import TokenUser

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientOut, status_code=201)
def create_client(payload: ClientIn, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    client = Client(user_id=user_uuid(user), **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    return db.query(Client).filter(Client.user_id == user_uuid(user)).order_by(Client.name).all()


@router.get("/{client_id}", response_model=ClientDetail)
def get_client(client_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    client = owned_client(client_id, db, user)
    detail = ClientDetail.model_validate(client)
    detail.meeting_count = db.query(Meeting).filter(Meeting.client_id == client.id).count()
    detail.pending_followups = (
        db.query(FollowUp)
        .filter(FollowUp.client_id == client.id, FollowUp.status == "pending")
        .count()
    )
    return detail


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: UUID, payload: ClientUpdate, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    client = owned_client(client_id, db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    db.delete(owned_client(client_id, db, user))
    db.commit()


@router.get("/{client_id}/timeline", response_model=list[TimelineItem])
def timeline(client_id: UUID, db: Session = Depends(get_db), user: TokenUser = Depends(get_current_user)):
    client = owned_client(client_id, db, user)
    meetings = (
        db.query(Meeting)
        .filter(Meeting.client_id == client.id)
        .order_by(Meeting.meeting_date.desc())
        .all()
    )
    return [
        TimelineItem(
            id=m.id,
            title=m.title,
            meeting_date=m.meeting_date,
            source=m.source,
            summary=m.summary,
            followup_count=len(m.followups),
        )
        for m in meetings
    ]
