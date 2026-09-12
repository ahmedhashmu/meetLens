"""Meeting ingestion service."""
from sqlalchemy.orm import Session
from app.models.meeting import Meeting
from app.models.schemas import MeetingCreate
from fastapi import HTTPException
import uuid


class MeetingIngestionService:
    """Service for ingesting meeting transcripts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_meeting(self, data: MeetingCreate) -> Meeting:
        """
        Create a new immutable meeting record.
        
        Args:
            data: Meeting creation data
            
        Returns:
            Created meeting record
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            # Create meeting instance
            meeting = Meeting(
                id=data.meetingId,
                contact_id=data.contactId,
                type=data.type,
                occurred_at=data.occurredAt,
                transcript=data.transcript
            )
            
            # Add to database
            self.db.add(meeting)
            self.db.commit()
            self.db.refresh(meeting)
            
            return meeting
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "CREATION_ERROR",
                    "message": f"Failed to create meeting: {str(e)}"
                }
            )
    
    def get_meeting(self, meeting_id: str) -> Meeting:
        """
        Retrieve a meeting by ID.
        
        Args:
            meeting_id: Meeting identifier
            
        Returns:
            Meeting record
            
        Raises:
            HTTPException: If meeting not found
        """
        meeting = self.db.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": "NOT_FOUND",
                    "message": f"Meeting {meeting_id} not found"
                }
            )
        
        return meeting