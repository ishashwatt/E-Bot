import os
import asyncio
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import Profile, AppliedCompany, EmailThread, EmailMessage, Attachment, NotificationLog, MailboxConfig
from app.services.attachment_parser import AttachmentParser
from app.services.relevance_engine import RelevanceEngine
from app.services.thread_tracker import ThreadTracker
from app.services.notifier import notifier
from app.services.live_mail_sync import LiveMailSyncService
from app.core.config import settings

router = APIRouter()

class AppliedCompanyCreateSchema(BaseModel):
    company_name: str
    role_title: Optional[str] = "Software Engineer / AI Trainee"
    status: Optional[str] = "Applied"
    notes: Optional[str] = ""

def get_or_sync_profile(db: Session) -> Profile:
    profile = db.query(Profile).first()
    if not profile:
        profile = Profile(
            name=settings.student_name,
            roll_number=settings.student_roll,
            neopat_id=settings.student_neopat,
            degree=settings.student_degree,
            branch=settings.student_branch,
            batch_year=settings.student_batch,
            tenth_percentage=settings.student_10th,
            twelfth_percentage=settings.student_12th,
            current_cgpa=settings.student_cgpa,
            standing_arrears=settings.student_arrears,
            custom_sound=settings.default_sound,
            telegram_chat_id=settings.telegram_chat_id,
            telegram_bot_token=settings.telegram_bot_token
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def get_or_sync_mailbox_config(db: Session) -> MailboxConfig:
    cfg = db.query(MailboxConfig).first()
    if not cfg:
        cfg = MailboxConfig(
            email_address=settings.college_email,
            app_password=settings.gmail_app_password,
            imap_server=settings.imap_server,
            imap_port=settings.imap_port,
            is_connected=bool(settings.college_email and settings.gmail_app_password),
            sync_interval_seconds=settings.sync_interval_seconds,
            fetch_limit=settings.fetch_limit
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg

@router.get("/profile")
def get_profile_endpoint(db: Session = Depends(get_db)):
    return get_or_sync_profile(db)

@router.get("/mail/config")
def get_mailbox_config(db: Session = Depends(get_db)):
    cfg = get_or_sync_mailbox_config(db)
    
    raw_email = settings.college_email or cfg.email_address or ""
    masked_email = raw_email
    if "@" in raw_email:
        user, domain = raw_email.split("@", 1)
        masked_user = user[:3] + "***" if len(user) > 3 else user + "***"
        masked_email = f"{masked_user}@{domain}"

    has_credentials = bool(settings.college_email and settings.gmail_app_password) or bool(cfg.email_address and cfg.app_password)

    return {
        "email_address": masked_email,
        "is_connected": cfg.is_connected or has_credentials,
        "is_configured_via_env": bool(settings.college_email and settings.gmail_app_password),
        "imap_server": settings.imap_server,
        "imap_port": settings.imap_port,
        "sync_interval_seconds": settings.sync_interval_seconds,
        "fetch_limit": settings.fetch_limit,
        "last_synced_at": cfg.last_synced_at.isoformat() if cfg.last_synced_at else None,
        "last_sync_error": cfg.last_sync_error,
        "total_emails_scanned": cfg.total_emails_scanned,
        "has_telegram": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "has_whatsapp": bool(settings.whatsapp_api_url)
    }

@router.post("/mail/sync-now")
async def sync_now(db: Session = Depends(get_db)):
    result = await asyncio.to_thread(LiveMailSyncService.sync_mailbox_sync, db)
    return result

@router.post("/mail/clear-all")
def clear_all_email_data(db: Session = Depends(get_db)):
    db.query(Attachment).delete()
    db.query(EmailMessage).delete()
    db.query(EmailThread).delete()
    db.query(NotificationLog).delete()
    
    cfg = get_or_sync_mailbox_config(db)
    cfg.total_emails_scanned = 0
    cfg.last_synced_at = None
    cfg.last_sync_error = ""
    db.commit()
    return {"message": "All email threads and history cleared successfully."}

@router.get("/applied-companies")
def get_applied_companies(db: Session = Depends(get_db)):
    return db.query(AppliedCompany).order_by(AppliedCompany.application_date.desc()).all()

@router.post("/applied-companies")
def add_applied_company(comp: AppliedCompanyCreateSchema, db: Session = Depends(get_db)):
    existing = db.query(AppliedCompany).filter(AppliedCompany.company_name.ilike(comp.company_name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company is already on your applied list")
    
    new_comp = AppliedCompany(
        company_name=comp.company_name.strip(),
        role_title=comp.role_title,
        status=comp.status,
        notes=comp.notes,
        last_update_summary="Added to applied watchlist"
    )
    db.add(new_comp)
    db.commit()
    db.refresh(new_comp)
    return new_comp

@router.delete("/applied-companies/{company_id}")
def delete_applied_company(company_id: int, db: Session = Depends(get_db)):
    comp = db.query(AppliedCompany).filter(AppliedCompany.id == company_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(comp)
    db.commit()
    return {"message": "Company removed from applied watchlist"}

@router.get("/threads")
def get_threads(priority_filter: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(EmailThread)
    if priority_filter and priority_filter != "All":
        query = query.filter(EmailThread.priority == priority_filter)
    threads = query.order_by(EmailThread.latest_received_at.desc()).all()
    
    result = []
    for t in threads:
        msg_count = len(t.messages)
        result.append({
            "id": t.id,
            "thread_id": t.thread_id,
            "subject": t.subject,
            "company_name": t.company_name,
            "category": t.category,
            "priority": t.priority,
            "is_applied_company": t.is_applied_company,
            "has_identity_match": t.has_identity_match,
            "status_summary": t.status_summary,
            "latest_received_at": t.latest_received_at.isoformat() if t.latest_received_at else None,
            "message_count": msg_count,
            "messages": [
                {
                    "id": m.id,
                    "message_id": m.message_id,
                    "sender": m.sender,
                    "subject": m.subject,
                    "body_text": m.body_text,
                    "received_at": m.received_at.isoformat() if m.received_at else None,
                    "is_trailing_mail": m.is_trailing_mail,
                    "change_summary": m.change_summary,
                    "matched_identity": m.matched_identity,
                    "matched_identity_details": m.matched_identity_details or [],
                    "matched_applied_company": m.matched_applied_company,
                    "eligibility_status": m.eligibility_status,
                    "eligibility_notes": m.eligibility_notes,
                    "attachments": [
                        {
                            "id": a.id,
                            "filename": a.filename,
                            "file_type": a.file_type,
                            "has_match": a.has_match,
                            "match_locations": a.match_locations or [],
                            "total_pages": a.total_pages
                        } for a in m.attachments
                    ]
                } for m in t.messages
            ]
        })
    return result

@router.post("/scan-custom-file")
async def scan_custom_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    profile = get_or_sync_profile(db)
    os.makedirs("uploaded_temp", exist_ok=True)
    temp_path = os.path.join("uploaded_temp", file.filename)
    
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    search_terms = [profile.roll_number, profile.neopat_id, profile.name]
    if profile.name_variations:
        search_terms.extend(profile.name_variations)

    result = AttachmentParser.parse_attachment(temp_path, search_terms)
    
    return {
        "filename": file.filename,
        "total_pages": result.get("total_pages", 1),
        "matches_found": len(result.get("matches", [])),
        "matches": result.get("matches", []),
        "preview": result.get("preview", "")
    }

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    return db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(50).all()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await notifier.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notifier.disconnect(websocket)

