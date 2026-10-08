"""Shared FastAPI dependencies — auth aur ownership checks."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.models import Client, FollowUp, Meeting
from app.services.security import TokenUser, decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> TokenUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login zaroori hai.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = decode_access_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ghalat ya expire ho chuka hai.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def user_uuid(user: TokenUser) -> uuid.UUID:
    return uuid.UUID(user.id)


def _is_owner(client: Client, user: TokenUser) -> bool:
    return client.user_id is not None and client.user_id == user_uuid(user)


def owned_client(client_id: uuid.UUID, db: Session, user: TokenUser) -> Client:
    """Client nikalta hai lekin sirf tab jab wo isi user ka ho."""
    client = db.get(Client, client_id)
    if client is None or not _is_owner(client, user):
        raise HTTPException(status_code=404, detail="Client nahi mila.")
    return client


def owned_meeting(meeting_id: uuid.UUID, db: Session, user: TokenUser) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or not _is_owner(meeting.client, user):
        raise HTTPException(status_code=404, detail="Meeting nahi mili.")
    return meeting


def owned_followup(followup_id: uuid.UUID, db: Session, user: TokenUser) -> FollowUp:
    followup = db.get(FollowUp, followup_id)
    if followup is None or not _is_owner(followup.client, user):
        raise HTTPException(status_code=404, detail="Follow-up nahi mila.")
    return followup
