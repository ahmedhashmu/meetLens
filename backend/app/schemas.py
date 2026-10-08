"""Request / response models."""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


FollowUpStatus = Literal["pending", "done", "dropped"]


# ---- Auth ---------------------------------------------------------
class UserOut(BaseModel):
    id: str
    email: str | None


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

    @field_validator("name")
    @classmethod
    def name_not_null(cls, value):
        # Naam khaali (null) nahi ho sakta — database mein NOT NULL hai
        if value is None:
            raise ValueError("name khaali nahi ho sakta")
        return value


class ClientOut(ORM):
    id: UUID
    name: str
    company: str | None
    email: str | None
    notes: str | None
    created_at: datetime


class ClientDetail(ClientOut):
    meeting_count: int = 0
    pending_followups: int = 0


# ---- Analysis -----------------------------------------------------
class AnalysisOut(ORM):
    summary: str | None
    topics: list[str]
    concerns: list[str]
    model_used: str | None
    analyzed_at: datetime | None


# ---- Meetings -----------------------------------------------------
class MeetingIn(BaseModel):
    client_id: UUID
    title: str = Field(min_length=1, max_length=200)
    meeting_date: date
    transcript: str = Field(min_length=20)


class MeetingOut(ORM):
    id: UUID
    client_id: UUID
    title: str
    meeting_date: date
    source: str
    audio_filename: str | None
    summary: str | None
    topics: list[str]
    concerns: list[str]
    analyzed_at: datetime | None
    created_at: datetime


class MeetingDetail(MeetingOut):
    transcript: str
    model_used: str | None
    followups: list["FollowUpOut"] = []


class TimelineItem(ORM):
    id: UUID
    title: str
    meeting_date: date
    source: str
    summary: str | None = None
    followup_count: int = 0


# ---- Follow-ups ---------------------------------------------------
class FollowUpIn(BaseModel):
    client_id: UUID
    meeting_id: UUID | None = None
    body: str = Field(min_length=1)
    owner: str | None = Field(default=None, max_length=120)
    due_date: date | None = None


class FollowUpUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1)
    owner: str | None = Field(default=None, max_length=120)
    due_date: date | None = None
    status: FollowUpStatus | None = None


class FollowUpOut(ORM):
    id: UUID
    client_id: UUID
    meeting_id: UUID | None
    body: str
    owner: str | None
    due_date: date | None
    status: str
    source: str
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
    meeting_id: UUID
    client_id: UUID
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
