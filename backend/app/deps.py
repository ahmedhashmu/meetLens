"""Shared FastAPI dependencies — auth aur ownership checks."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Client, Meeting, User
from app.services.security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login zaroori hai.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(credentials.credentials)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ghalat ya expire ho chuka hai.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def owned_client(client_id: str, db: Session, user: User) -> Client:
    """Client nikalta hai lekin sirf tab jab wo isi user ka ho."""
    client = db.get(Client, client_id)
    if client is None or client.user_id != user.id:
        raise HTTPException(status_code=404, detail="Client nahi mila.")
    return client


def owned_meeting(meeting_id: str, db: Session, user: User) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if meeting is None or meeting.client.user_id != user.id:
        raise HTTPException(status_code=404, detail="Meeting nahi mili.")
    return meeting
