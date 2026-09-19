"""Database tables — users, clients, meetings, analyses, followups."""
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """App ka user — consulting firm ka employee."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    clients: Mapped[list["Client"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Client(Base):
    """Consulting firm ka client. Har client ek hi user ka hota hai."""

    __tablename__ = "clients"
    __table_args__ = (Index("ix_clients_user_name", "user_id", "name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    company: Mapped[str | None] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="clients")
    meetings: Mapped[list["Meeting"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class Meeting(Base):
    """Ek meeting — transcript paste kiya gaya ya audio se banaya gaya."""

    __tablename__ = "meetings"
    __table_args__ = (Index("ix_meetings_client_date", "client_id", "meeting_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    # "paste" = user ne transcript likha, "audio" = Whisper ne banaya
    source: Mapped[str] = mapped_column(String(20), default="paste", nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    audio_filename: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    client: Mapped[Client] = relationship(back_populates="meetings")
    analysis: Mapped["Analysis | None"] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", uselist=False
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="meeting", cascade="all, delete-orphan"
    )


class Analysis(Base):
    """AI ka natija — summary, topics, concerns. Har meeting ka ek."""

    __tablename__ = "analyses"
    __table_args__ = (UniqueConstraint("meeting_id", name="uq_analyses_meeting"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    meeting_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    concerns: Mapped[list] = mapped_column(JSON, default=list)
    model_used: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    meeting: Mapped[Meeting] = relationship(back_populates="analysis")


class FollowUp(Base):
    """Meeting se nikla hua follow-up item — owner, due date aur status ke saath."""

    __tablename__ = "followups"
    __table_args__ = (Index("ix_followups_client_status", "client_id", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("clients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    meeting_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(120))
    due_date: Mapped[date | None] = mapped_column(Date)
    # "pending" ya "done"
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    client: Mapped[Client] = relationship(back_populates="followups")
    meeting: Mapped[Meeting | None] = relationship(back_populates="followups")
