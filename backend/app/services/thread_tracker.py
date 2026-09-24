from sqlalchemy.orm import Session
from app.db.models import EmailThread, EmailMessage, AppliedCompany, Attachment, NotificationLog
from typing import Dict, Any, List, Optional
from datetime import datetime

class ThreadTracker:
    """
    Manages grouping of incoming messages into discussion threads and tracks application stages.
    """

    @staticmethod
    def get_or_create_thread(
        db: Session,
        thread_id: str,
        subject: str,
        company_name: Optional[str] = None
    ) -> EmailThread:
        thread = db.query(EmailThread).filter(EmailThread.thread_id == thread_id).first()
        if not thread:
            clean_sub = subject.replace("Re:", "").replace("RE:", "").replace("Fwd:", "").replace("FWD:", "").strip()
            thread = EmailThread(
                thread_id=thread_id,
                subject=clean_sub,
                company_name=company_name,
                category="General",
                priority="Low",
                is_applied_company=False,
                has_identity_match=False,
                status_summary="Thread initiated",
                latest_received_at=datetime.utcnow(),
                message_count=1
            )
            db.add(thread)
            db.commit()
            db.refresh(thread)
        else:
            thread.message_count += 1
            thread.latest_received_at = datetime.utcnow()
            if company_name and not thread.company_name:
                thread.company_name = company_name
            db.commit()
            db.refresh(thread)
        return thread

    @staticmethod
    def update_company_status_from_thread(
        db: Session,
        company_name: str,
        evaluation: Dict[str, Any],
        subject: str
    ):
        if not company_name:
            return
        
        company = db.query(AppliedCompany).filter(
            AppliedCompany.company_name.ilike(company_name)
        ).first()

        if company:
            company.last_mail_date = datetime.utcnow()
            if evaluation.get("matched_identity"):
                company.status = "Shortlisted / Action Req."
                company.last_update_summary = f"Identity Match in: {subject}"
            elif evaluation.get("is_trailing_update"):
                if "interview" in subject.lower():
                    company.status = "Interview"
                elif "shortlist" in subject.lower():
                    company.status = "Shortlisted"
                elif "assessment" in subject.lower() or "test" in subject.lower():
                    company.status = "Assessment"
                company.last_update_summary = evaluation.get("change_summary", "Trailing update received.")
            db.commit()
