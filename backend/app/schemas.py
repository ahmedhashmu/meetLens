"""Request / response models."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth ---------------------------------------------------------
class SignupIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORM):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Clients ------------------------------------------------------
class ClientIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    company: str | None = Field(default=None, max_length=160)
    email: EmailStr | None = None
    notes: str | None = None


class ClientOut(ORM):
    id: str
    name: str
    company: str | None
    email: EmailStr | None
    notes: str | None
    created_at: datetime


class ClientDetail(ClientOut):
    meeting_count: int = 0
    pending_followups: int = 0


# ---- Analysis -----------------------------------------------------
class AnalysisOut(ORM):
    id: str
    summary: str
    topics: list[str]
    concerns: list[str]
    model_used: str | None
    created_at: datetime


# ---- Meetings -----------------------------------------------------
class MeetingIn(BaseModel):
    client_id: str
    title: str = Field(min_length=1, max_length=200)
    meeting_date: date
    transcript: str = Field(min_length=20)


class MeetingOut(ORM):
    id: str
    client_id: str
    title: str
    meeting_date: date
    source: str
    audio_filename: str | None
    created_at: datetime


class MeetingDetail(MeetingOut):
    transcript: str
    analysis: AnalysisOut | None = None
    followups: list["FollowUpOut"] = []


class TimelineItem(ORM):
    id: str
    title: str
    meeting_date: date
    source: str
    summary: str | None = None
    followup_count: int = 0


# ---- Follow-ups ---------------------------------------------------
class FollowUpIn(BaseModel):
    client_id: str
    meeting_id: str | None = None
    text: str = Field(min_length=1)
    owner: str | None = Field(default=None, max_length=120)
    due_date: date | None = None


class FollowUpUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    owner: str | None = Field(default=None, max_length=120)
    due_date: date | None = None
    status: str | None = Field(default=None, pattern="^(pending|done)$")


class FollowUpOut(ORM):
    id: str
    client_id: str
    meeting_id: str | None
    text: str
    owner: str | None
    due_date: date | None
    status: str
    created_at: datetime
    completed_at: datetime | None


# ---- Dashboard / search -------------------------------------------
class DashboardOut(BaseModel):
    total_clients: int
    total_meetings: int
    pending_followups: int
    overdue_followups: int
    done_followups: int
    recent_meetings: list[MeetingOut]
    upcoming_followups: list[FollowUpOut]


class SearchHit(BaseModel):
    meeting_id: str
    client_id: str
    client_name: str
    title: str
    meeting_date: date
    snippet: str
    matched_in: str


class SearchOut(BaseModel):
    query: str
    count: int
    results: list[SearchHit]


class ReminderResult(BaseModel):
    sent: int
    skipped: int
    detail: str


MeetingDetail.model_rebuild()
