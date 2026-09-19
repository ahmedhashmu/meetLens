"""Pending follow-ups ki email reminders."""
import logging
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Client, FollowUp, User

logger = logging.getLogger(__name__)


def _build_message(user: User, rows: list[tuple[FollowUp, Client]]) -> EmailMessage:
    lines = [f"Assalam-o-alaikum {user.name},", "", "Ye aapke pending follow-up items hain:", ""]
    for followup, client in rows:
        due = followup.due_date.isoformat() if followup.due_date else "koi due date nahi"
        owner = followup.owner or "assign nahi hua"
        lines.append(f"- [{client.name}] {followup.text}")
        lines.append(f"    owner: {owner} | due: {due}")
    lines += ["", "— MeetLens"]

    msg = EmailMessage()
    msg["Subject"] = f"MeetLens — {len(rows)} pending follow-up(s)"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER or ""
    msg["To"] = user.email
    msg.set_content("\n".join(lines))
    return msg


def _send(msg: EmailMessage) -> None:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_reminders(db: Session, user: User, within_days: int = 3) -> tuple[int, int, str]:
    """User ko unke due/overdue follow-ups ki ek reminder email bhejta hai.

    Wapas karta hai: (bheje gaye items, chhore gaye items, tafseel)
    """
    cutoff = date.today() + timedelta(days=within_days)

    rows = (
        db.query(FollowUp, Client)
        .join(Client, FollowUp.client_id == Client.id)
        .filter(
            Client.user_id == user.id,
            FollowUp.status == "pending",
            FollowUp.due_date.isnot(None),
            FollowUp.due_date <= cutoff,
        )
        .order_by(FollowUp.due_date.asc())
        .all()
    )

    if not rows:
        return 0, 0, "Koi due follow-up nahi hai."

    if not settings.email_enabled:
        return 0, len(rows), "SMTP settings .env mein nahi hain, is liye email nahi bheji."

    try:
        _send(_build_message(user, rows))
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("Reminder email failed for %s: %s", user.email, exc)
        return 0, len(rows), f"Email bhejne mein masla: {exc}"

    now = datetime.now(timezone.utc)
    for followup, _ in rows:
        followup.reminder_sent_at = now
    db.commit()

    return len(rows), 0, f"{user.email} par reminder bhej di gayi."
