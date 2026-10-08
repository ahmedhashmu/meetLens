"""Database tables — clients, meetings, followups.

Ye tables Supabase mein pehle se bani hain (frontend bhi inhi ko use karta hai).
Users ki table Supabase ki apni `auth.users` hai, is liye yahan nahi hai.
Backend ke extra columns `backend/sql/001_backend_columns.sql` mein hain.
"""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base

# Postgres mein text[]; local SQLite (tests) mein JSON
TextList = ARRAY(Text).with_variant(JSON(), "sqlite")


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Client(Base):
    """Consulting firm ka client. `user_id` = jis ne banaya (auth.users.id)."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    meetings: Mapped[list["Meeting"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", passive_deletes=True
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="client", cascade="all, delete-orphan", passive_deletes=True
    )


class Meeting(Base):
    """Ek meeting — transcript aur us ka AI analysis (summary, topics, concerns)."""

    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    # "paste" = user ne transcript likha, "audio" = Whisper ne banaya
    source: Mapped[str] = mapped_column(Text, default="paste", nullable=False)
    audio_filename: Mapped[str | None] = mapped_column(Text)

    # AI analysis — analyze karne se pehle khaali
    summary: Mapped[str | None] = mapped_column(Text)
    topics: Mapped[list[str]] = mapped_column(TextList, default=list, nullable=False)
    concerns: Mapped[list[str]] = mapped_column(TextList, default=list, nullable=False)
    model_used: Mapped[str | None] = mapped_column(Text)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    client: Mapped[Client] = relationship(back_populates="meetings")
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True
    )


class FollowUp(Base):
    """Follow-up item — owner, due date aur status ke saath."""

    __tablename__ = "followups"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    meeting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    # "pending", "done" ya "dropped"
    status: Mapped[str] = mapped_column(Text, default="pending", nullable=False)
    # "ai" = analysis ne banaya, "manual" = user ne khud likha
    source: Mapped[str] = mapped_column(Text, default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[Client] = relationship(back_populates="followups")
    meeting: Mapped[Meeting | None] = relationship(back_populates="followups")
