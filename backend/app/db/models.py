from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Shashwat Pratap Singh")
    name_variations = Column(JSON, default=lambda: ["Shashwat Pratap Singh", "Shashwat Pratap", "Shashwat Singh", "Shashwat", "S P Singh", "23BAI11174"])
    roll_number = Column(String, default="23BAI11174", index=True)
    neopat_id = Column(String, default="S4Z5F7U9", index=True)
    degree = Column(String, default="B.Tech")
    branch = Column(String, default="CSE (AI & ML)")
    batch_year = Column(Integer, default=2027)
    tenth_percentage = Column(Float, default=72.6)
    twelfth_percentage = Column(Float, default=69.0)
    current_cgpa = Column(Float, default=7.85)
    standing_arrears = Column(Integer, default=0)
    telegram_chat_id = Column(String, default="")
    telegram_bot_token = Column(String, default="")
    custom_sound = Column(String, default="urgent_ping")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MailboxConfig(Base):
    __tablename__ = "mailbox_configs"

    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String, default="")
    app_password = Column(String, default="")
    imap_server = Column(String, default="imap.gmail.com")
    imap_port = Column(Integer, default=993)
    is_connected = Column(Boolean, default=False)
    sync_interval_seconds = Column(Integer, default=60)
    fetch_limit = Column(Integer, default=25)
    unread_only = Column(Boolean, default=False)
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_error = Column(Text, default="")
    total_emails_scanned = Column(Integer, default=0)

class AppliedCompany(Base):
    __tablename__ = "applied_companies"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True)
    role_title = Column(String, default="Software Engineer / AI Trainee")
    status = Column(String, default="Applied")
    application_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, default="")
    last_update_summary = Column(Text, default="")
    last_mail_date = Column(DateTime, nullable=True)

class EmailThread(Base):
    __tablename__ = "email_threads"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True)
    subject = Column(String, index=True)
    company_name = Column(String, nullable=True, index=True)
    category = Column(String, default="General")
    priority = Column(String, default="Low")
    is_applied_company = Column(Boolean, default=False)
    has_identity_match = Column(Boolean, default=False)
    status_summary = Column(Text, default="")
    latest_received_at = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=1)
    
    messages = relationship("EmailMessage", back_populates="thread", cascade="all, delete-orphan")

class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    thread_id = Column(String, ForeignKey("email_threads.thread_id"), index=True)
    sender = Column(String)
    recipient = Column(String)
    subject = Column(String)
    body_text = Column(Text)
    body_html = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    is_trailing_mail = Column(Boolean, default=False)
    change_summary = Column(Text, default="")
    
    matched_identity = Column(Boolean, default=False)
    matched_identity_details = Column(JSON, default=list)
    matched_applied_company = Column(Boolean, default=False)
    eligibility_status = Column(String, default="Unknown")
    eligibility_notes = Column(Text, default="")
    
    thread = relationship("EmailThread", back_populates="messages")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("email_messages.message_id"), index=True)
    filename = Column(String)
    file_type = Column(String)
    file_path = Column(String, nullable=True)
    extracted_text_preview = Column(Text, default="")
    has_match = Column(Boolean, default=False)
    match_locations = Column(JSON, default=list)
    total_pages = Column(Integer, default=1)

    message = relationship("EmailMessage", back_populates="attachments")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, nullable=True)
    title = Column(String)
    content = Column(Text)
    priority = Column(String)
    notification_type = Column(String)
    sound_played = Column(String, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
