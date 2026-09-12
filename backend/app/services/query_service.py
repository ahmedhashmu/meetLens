"""Query service for retrieving meeting data."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.meeting import Meeting
from app.models.meeting_analysis import MeetingAnalysis
from app.models.schemas import (
    MeetingWithAnalysis, 
    MeetingAnalysisResponse,
    MeetingBasicView
)
from typing import List, Union


class QueryService:
    """Service for querying meeting data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_contact_meetings(
        self, 
        contact_id: str, 
        user_role: str = "operator"
    ) -> List[Union[MeetingWithAnalysis, MeetingBasicView]]:
        """
        Get all meetings for a contact with role-based filtering.
        
        Args:
            contact_id: Contact identifier
            user_role: User role ('operator' or 'basic')
            
        Returns:
            List of meetings (full or limited based on role)
        """
        # Query meetings
        meetings = (
            self.db.query(Meeting)
            .filter(Meeting.contact_id == contact_id)
            .order_by(desc(Meeting.occurred_at))
            .all()
        )
        
        # Build response based on role
        result = []
        
        if user_role == "operator":
            # Operator: Full access (transcript + analysis)
            for meeting in meetings:
                # Get most recent analysis
                analysis = (
                    self.db.query(MeetingAnalysis)
                    .filter(MeetingAnalysis.meeting_id == meeting.id)
                    .order_by(desc(MeetingAnalysis.analyzed_at))
                    .first()
                )
                
                # Build meeting with analysis
                meeting_data = MeetingWithAnalysis(
                    id=meeting.id,
                    contactId=meeting.contact_id,
                    type=meeting.type,
                    occurredAt=meeting.occurred_at,
                    transcript=meeting.transcript,
                    createdAt=meeting.created_at,
                    analysis=MeetingAnalysisResponse(
                        id=analysis.id,
                        meetingId=analysis.meeting_id,
                        sentiment=analysis.sentiment,
                        topics=analysis.topics,
                        objections=analysis.objections,
                        commitments=analysis.commitments,
                        outcome=analysis.outcome,
                        summary=analysis.summary,
                        analyzedAt=analysis.analyzed_at
                    ) if analysis else None
                )
                
                result.append(meeting_data)
        
        else:  # basic user
            # Basic: Metadata only (no transcript, no analysis)
            for meeting in meetings:
                meeting_data = MeetingBasicView(
                    id=meeting.id,
                    contactId=meeting.contact_id,
                    type=meeting.type,
                    occurredAt=meeting.occurred_at,
                    createdAt=meeting.created_at
                )
                
                result.append(meeting_data)
        
        return result