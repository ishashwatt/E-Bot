from sqlalchemy.orm import Session
from app.db.models import EmailThread, EmailMessage, AppliedCompany, Attachment, NotificationLog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import hashlib

class ThreadTracker:
    """
    Manages grouping of incoming messages into discussion threads and tracks application stages.
    """

    @staticmethod
    def get_or_create_thread(
        db: Session,
        subject: str,
        sender: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        detected_company: Optional[str] = None,
        received_at: Optional[datetime] = None,
        thread_id: Optional[str] = None
    ) -> Tuple[EmailThread, bool]:
        clean_sub = re.sub(r'^(Re|RE|Fwd|FWD|fwd|re):\s*', '', subject, flags=re.IGNORECASE).strip()
        
        # Determine consistent thread key
        if not thread_id:
            if in_reply_to:
                thread_id = in_reply_to.strip()
            else:
                # Group by normalized subject hash
                sub_norm = re.sub(r'\s+', ' ', clean_sub.lower())
                thread_id = f"th_{hashlib.md5(sub_norm.encode('utf-8')).hexdigest()[:12]}"

        thread = db.query(EmailThread).filter(EmailThread.thread_id == thread_id).first()
        is_new = False
        
        if not thread:
            is_new = True
            thread = EmailThread(
                thread_id=thread_id,
                subject=clean_sub,
                company_name=detected_company,
                category="General",
                priority="Low",
                is_applied_company=False,
                has_identity_match=False,
                status_summary="Thread initiated",
                latest_received_at=received_at or datetime.utcnow(),
                message_count=1
            )
            db.add(thread)
            db.commit()
            db.refresh(thread)
        else:
            thread.message_count += 1
            thread.latest_received_at = received_at or datetime.utcnow()
            if detected_company and not thread.company_name:
                thread.company_name = detected_company
            db.commit()
            db.refresh(thread)
            
        return thread, is_new

    @staticmethod
    def get_thread_history(db: Session, thread_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves earlier messages in this thread to provide contextual continuity.
        """
        if not thread_id:
            return []
        messages = (
            db.query(EmailMessage)
            .filter(EmailMessage.thread_id == thread_id)
            .order_by(EmailMessage.received_at.asc())
            .all()
        )
        return [
            {
                "subject": m.subject,
                "body": m.body_text or "",
                "received_at": m.received_at.isoformat() if m.received_at else ""
            }
            for m in messages
        ]

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
            AppliedCompany.company_name.ilike(company_name.strip())
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
