"""Analysis engine for LLM-powered meeting analysis."""
from sqlalchemy.orm import Session
from app.models.meeting_analysis import MeetingAnalysis
from app.services.llm_client import LLMClient
from app.services.ingestion import MeetingIngestionService
from fastapi import HTTPException
import uuid


class AnalysisEngine:
    """Engine for analyzing meeting transcripts."""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_client = LLMClient()
        self.ingestion_service = MeetingIngestionService(db)
    
    def analyze_meeting(self, meeting_id: str) -> MeetingAnalysis:
        """
        Analyze a meeting transcript using bounded LLM agent.
        
        Args:
            meeting_id: ID of meeting to analyze
            
        Returns:
            Analysis record
            
        Raises:
            HTTPException: If meeting not found or analysis fails
        """
        try:
            # Retrieve meeting
            meeting = self.ingestion_service.get_meeting(meeting_id)
            
            # Extract signals using LLM
            signals = self.llm_client.extract_signals(meeting.transcript)
            
            # Create analysis record
            analysis = MeetingAnalysis(
                id=str(uuid.uuid4()),
                meeting_id=meeting_id,
                sentiment=signals.sentiment,
                topics=signals.topics,
                objections=signals.objections,
                commitments=signals.commitments,
                outcome=signals.outcome,
                summary=signals.summary
            )
            
            # Persist analysis
            self.db.add(analysis)
            self.db.commit()
            self.db.refresh(analysis)
            
            return analysis
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "ANALYSIS_ERROR",
                    "message": f"Failed to analyze meeting: {str(e)}"
                }
            )
    
    def get_analysis(self, meeting_id: str) -> MeetingAnalysis | None:
        """
        Get the most recent analysis for a meeting.
        
        Args:
            meeting_id: Meeting identifier
            
        Returns:
            Most recent analysis or None
        """
        return (
            self.db.query(MeetingAnalysis)
            .filter(MeetingAnalysis.meeting_id == meeting_id)
            .order_by(MeetingAnalysis.analyzed_at.desc())
            .first()
        )