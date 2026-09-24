import os
import imaplib
import email
from email.header import decode_header
import re
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import MailboxConfig, EmailThread, EmailMessage, Attachment, NotificationLog, Profile, AppliedCompany
from app.services.attachment_parser import AttachmentParser
from app.services.relevance_engine import RelevanceEngine
from app.services.thread_tracker import ThreadTracker
from app.services.notifier import notifier
from app.core.config import settings

logger = logging.getLogger("live_mail_sync")

DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "downloads_attachments")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# IST Timezone (UTC + 5:30)
IST_OFFSET = timezone(timedelta(hours=5, minutes=30))
_last_transition_date: Optional[str] = None


class LiveMailSyncService:
    @staticmethod
    def clean_header_str(header_val: Any) -> str:
        if not header_val:
            return ""
        decoded_fragments = decode_header(header_val)
        result = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                try:
                    result.append(fragment.decode(encoding or "utf-8", errors="ignore"))
                except Exception:
                    result.append(fragment.decode("latin-1", errors="ignore"))
            else:
                result.append(str(fragment))
        return "".join(result).strip()

    @classmethod
    def check_and_send_date_transition(cls, db: Session):
        """
        Automatically sends a Telegram briefing alert when the date rolls over after 12:00 AM midnight (IST).
        """
        global _last_transition_date
        now_ist = datetime.now(IST_OFFSET)
        today_key = now_ist.strftime("%Y-%m-%d")

        if _last_transition_date is None:
            # First boot during current day: store date key
            _last_transition_date = today_key
            logger.info(f"Initialized midnight date tracker for {today_key}")
            return

        if _last_transition_date != today_key:
            _last_transition_date = today_key
            logger.info(f"Midnight transition detected: New date is {today_key}. Sending Telegram briefing.")
            
            date_formatted = now_ist.strftime("%A, %d %B %Y")
            time_formatted = now_ist.strftime("%I:%M %p IST")
            
            profile = db.query(Profile).first()
            student_name = profile.name if profile else settings.student_name
            roll_no = profile.roll_number if profile else settings.student_roll
            branch = profile.branch if profile else settings.student_branch
            batch = profile.batch_year if profile else settings.student_batch

            briefing_msg = (
                f"🌅 <b>NEW DAY BRIEFING | {date_formatted.upper()}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📅 <b>Today's Date:</b> <b>{date_formatted}</b>\n"
                f"⏰ <b>System Time:</b> <b>{time_formatted} (Midnight Alert)</b>\n"
                f"🟢 <b>E-Bot Status:</b> <b>Active & Monitoring 24/7</b>\n\n"
                f"👤 <b>Active Profile:</b>\n"
                f"  • <b>{student_name}</b> (<code>{roll_no}</code>)\n"
                f"  • {branch} | Batch {batch}\n\n"
                f"🛡️ <b>Real-Time Inbox Watch:</b>\n"
                f"  • Placement Drives & Dynamic Eligibility Filtering\n"
                f"  • OA / Interview Shortlists & Selection Lists\n"
                f"  • CDC & Program Chair Updates\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>E-Bot is active and ready to deliver real-time notifications for all new updates.</i>"
            )
            try:
                notifier.send_telegram_alert(briefing_msg)
            except Exception as ex:
                logger.error(f"Failed to send midnight date briefing on Telegram: {ex}")

    @classmethod
    def test_connection(cls, email_address: str, app_password: str, server: str = "imap.gmail.com", port: int = 993) -> Dict[str, Any]:
        try:
            clean_pw = app_password.replace(" ", "").strip()
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(email_address.strip(), clean_pw)
            status, counts = mail.select("INBOX", readonly=True)
            mail.logout()
            return {
                "success": True,
                "message": f"Successfully connected to {email_address} via IMAP SSL!",
                "total_inbox_messages": int(counts[0].decode()) if counts and counts[0] else 0
            }
        except Exception as e:
            err_msg = str(e)
            if "AUTHENTICATIONFAILED" in err_msg or "Application-specific password required" in err_msg:
                err_msg = "Authentication Failed: Please check your 16-character Google App Password in .env."
            return {
                "success": False,
                "message": f"Connection failed: {err_msg}"
            }

    @classmethod
    def sync_mailbox_sync(cls, db: Session, limit: Optional[int] = None) -> Dict[str, Any]:
        # First, check if midnight rollover occurred
        cls.check_and_send_date_transition(db)

        email_addr = settings.college_email
        app_pw = settings.gmail_app_password
        server = settings.imap_server
        port = settings.imap_port
        fetch_lim = limit or settings.fetch_limit or 30

        config = db.query(MailboxConfig).first()
        if not email_addr or not app_pw:
            if config and config.email_address and config.app_password:
                email_addr = config.email_address
                app_pw = config.app_password
                server = config.imap_server
                port = config.imap_port
            else:
                return {
                    "status": "waiting",
                    "message": "Mailbox credentials not set in backend .env file (COLLEGE_EMAIL / GMAIL_APP_PASSWORD)."
                }

        profile = db.query(Profile).first()
        profile_dict = {
            "name": profile.name if profile else settings.student_name,
            "roll_number": profile.roll_number if profile else settings.student_roll,
            "neopat_id": profile.neopat_id if profile else settings.student_neopat,
            "name_variations": [settings.student_name, settings.student_roll, "Shashwat", "Shashwat Singh"],
            "degree": profile.degree if profile else settings.student_degree,
            "branch": profile.branch if profile else settings.student_branch,
            "batch_year": profile.batch_year if profile else settings.student_batch,
            "tenth_percentage": profile.tenth_percentage if profile else settings.student_10th,
            "twelfth_percentage": profile.twelfth_percentage if profile else settings.student_12th,
            "current_cgpa": profile.current_cgpa if profile else settings.student_cgpa
        }

        clean_pw = app_pw.replace(" ", "").strip()
        synced_count = 0
        new_alerts = 0

        try:
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(email_addr.strip(), clean_pw)
            mail.select("INBOX")

            status, messages = mail.search(None, "ALL")
            if status != "OK" or not messages[0]:
                mail.logout()
                if config:
                    config.is_connected = True
                    config.last_synced_at = datetime.utcnow()
                    config.last_sync_error = ""
                    db.commit()
                return {"status": "success", "message": "Inbox checked. No new unread messages.", "synced": 0}

            msg_ids = messages[0].split()
            target_ids = msg_ids[-fetch_lim:]
            target_ids.reverse()

            applied_list = [c.company_name for c in db.query(AppliedCompany).all()]

            for m_id in target_ids:
                res, msg_data = mail.fetch(m_id, "(RFC822)")
                if res != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = cls.clean_header_str(msg.get("Subject", "(No Subject)"))
                sender = cls.clean_header_str(msg.get("From", ""))
                recipient = cls.clean_header_str(msg.get("To", email_addr))
                msg_uid = cls.clean_header_str(msg.get("Message-ID", f"imap_{m_id.decode()}"))
                in_reply_to = cls.clean_header_str(msg.get("In-Reply-To", ""))

                existing_msg = db.query(EmailMessage).filter(EmailMessage.message_id == msg_uid).first()
                if existing_msg:
                    continue

                body_text = ""
                body_html = ""
                saved_attachments = []

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))

                        if "attachment" in content_disposition or part.get_filename():
                            filename = cls.clean_header_str(part.get_filename())
                            if filename:
                                file_ext = os.path.splitext(filename)[1].lower()
                                safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
                                file_path = os.path.join(DOWNLOADS_DIR, safe_name)
                                payload = part.get_payload(decode=True)
                                if payload:
                                    with open(file_path, "wb") as f:
                                        f.write(payload)
                                    saved_attachments.append({
                                        "filename": filename,
                                        "file_type": file_ext,
                                        "file_path": file_path
                                    })
                        elif content_type == "text/plain" and not body_text:
                            payload = part.get_payload(decode=True)
                            if payload:
                                try:
                                    body_text = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                                except Exception:
                                    body_text = payload.decode("latin-1", errors="ignore")
                        elif content_type == "text/html" and not body_html:
                            payload = part.get_payload(decode=True)
                            if payload:
                                try:
                                    body_html = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                                except Exception:
                                    body_html = payload.decode("latin-1", errors="ignore")
                else:
                    content_type = msg.get_content_type()
                    payload = msg.get_payload(decode=True)
                    if payload:
                        decoded = ""
                        try:
                            decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
                        except Exception:
                            decoded = payload.decode("latin-1", errors="ignore")
                        if content_type == "text/html":
                            body_html = decoded
                            body_text = re.sub(r'<[^>]+>', ' ', decoded)
                        else:
                            body_text = decoded

                parsed_attachments = []
                search_terms = [profile_dict["roll_number"], profile_dict["neopat_id"], profile_dict["name"]]
                for att in saved_attachments:
                    parse_res = AttachmentParser.parse_and_search(att["file_path"], search_terms)
                    parsed_attachments.append({
                        "filename": att["filename"],
                        "file_type": att["file_type"],
                        "file_path": att["file_path"],
                        "matches": parse_res["matches"],
                        "preview": parse_res["preview"],
                        "total_pages": parse_res.get("total_pages", 1)
                    })

                date_header = msg.get("Date")
                received_dt = datetime.utcnow()
                if date_header:
                    try:
                        parsed_dt = email.utils.parsedate_to_datetime(date_header)
                        if parsed_dt:
                            received_dt = parsed_dt.astimezone(timezone.utc).replace(tzinfo=None)
                    except Exception:
                        pass

                temp_eval = RelevanceEngine.evaluate_email(
                    subject=subject,
                    body=body_text,
                    attachments_data=parsed_attachments,
                    profile_data=profile_dict,
                    body_html=body_html,
                    sender=sender,
                    applied_companies=applied_list
                )

                thread, is_new_thread = ThreadTracker.get_or_create_thread(
                    db=db,
                    subject=subject,
                    sender=sender,
                    in_reply_to=in_reply_to,
                    detected_company=temp_eval.get("company_name"),
                    received_at=received_dt
                )

                prev_messages = ThreadTracker.get_thread_history(db, thread.thread_id)

                evaluation = RelevanceEngine.evaluate_email(
                    subject=subject,
                    body=body_text,
                    attachments_data=parsed_attachments,
                    profile_data=profile_dict,
                    body_html=body_html,
                    sender=sender,
                    applied_companies=applied_list,
                    previous_thread_messages=prev_messages
                )

                final_company = evaluation.get("company_name") or thread.company_name

                new_msg_record = EmailMessage(
                    message_id=msg_uid,
                    thread_id=thread.thread_id,
                    subject=subject,
                    sender=sender,
                    recipient=recipient,
                    body_text=body_text,
                    body_html=body_html,
                    received_at=received_dt,
                    priority=evaluation["priority"],
                    category=evaluation["category"],
                    company_name=final_company,
                    venues=evaluation.get("venues", []),
                    slots=evaluation.get("slots", []),
                    action_links=evaluation.get("links", []),
                    deadline_date_time=evaluation.get("deadline_date_time"),
                    schedule_date_time=evaluation.get("schedule_date_time"),
                    reason=evaluation["reason"],
                    matched_identity=evaluation["matched_identity"],
                    matched_identity_details=evaluation.get("matched_identity_details", []),
                    matched_applied_company=evaluation.get("matched_applied_company", False),
                    eligibility_status=evaluation.get("eligibility_status", "Neutral"),
                    eligibility_notes=evaluation.get("eligibility_notes", "")
                )
                db.add(new_msg_record)
                db.commit()
                db.refresh(new_msg_record)

                for att in parsed_attachments:
                    has_m = len(att.get("matches", [])) > 0
                    db_att = Attachment(
                        message_id=msg_uid,
                        filename=att["filename"],
                        file_type=att["file_type"],
                        file_path=att["file_path"],
                        extracted_text_preview=att.get("preview", ""),
                        has_match=has_m,
                        match_locations=att.get("matches", []),
                        total_pages=att.get("total_pages", 1)
                    )
                    db.add(db_att)
                db.commit()

                if final_company:
                    ThreadTracker.update_company_status_from_thread(db, final_company, evaluation, subject)

                # Send Telegram Notification
                if evaluation.get("telegram_notify") and evaluation.get("telegram_message"):
                    new_alerts += 1
                    notifier.send_telegram_alert(evaluation["telegram_message"])

                # Trigger In-App Sound and Broadcast WebSockets
                if evaluation.get("trigger_sound"):
                    sound_choice = profile.custom_sound if profile else "urgent_ping"
                    log_entry = NotificationLog(
                        message_id=msg_uid,
                        title=f"[{evaluation['priority'].upper()}] {subject}",
                        content=evaluation["reason"],
                        priority=evaluation["priority"],
                        notification_type="Sound + Telegram Push",
                        sound_played=sound_choice
                    )
                    db.add(log_entry)
                    db.commit()

                    alert_payload = {
                        "type": "NEW_ALERT",
                        "priority": evaluation["priority"],
                        "sound": sound_choice,
                        "sound_type": evaluation.get("sound_type", "urgent_ping"),
                        "title": f"[{evaluation['priority'].upper()}] {subject}",
                        "reason": evaluation["reason"],
                        "thread_id": thread.thread_id,
                        "company_name": final_company,
                        "received_at": datetime.utcnow().isoformat()
                    }
                    notifier.broadcast_alert_sync(alert_payload)

                synced_count += 1

            mail.logout()

            if config:
                config.email_address = email_addr
                config.is_connected = True
                config.last_synced_at = datetime.utcnow()
                config.last_sync_error = ""
                config.total_emails_scanned += synced_count
                db.commit()

            return {
                "status": "success",
                "message": f"Synchronized successfully. Scanned {synced_count} emails.",
                "new_emails": synced_count,
                "alerts_triggered": new_alerts
            }

        except Exception as e:
            if config:
                config.is_connected = False
                config.last_sync_error = str(e)
                db.commit()
            return {"status": "error", "message": f"Sync Error: {str(e)}"}

async def start_background_mail_sync(interval_seconds: int = 60):
    await asyncio.sleep(3)
    while True:
        try:
            db = SessionLocal()
            await asyncio.to_thread(LiveMailSyncService.sync_mailbox_sync, db)
            db.close()
        except Exception as e:
            logger.error(f"Error in background mail sync loop: {e}")
        await asyncio.sleep(settings.sync_interval_seconds or interval_seconds)
