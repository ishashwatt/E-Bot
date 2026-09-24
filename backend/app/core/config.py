import os
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=ENV_PATH, override=True)

class Settings(BaseModel):
    app_name: str = "E-Bot - College Mail Intelligence"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ebot.db")
    
    college_email: str = os.getenv("COLLEGE_EMAIL", "")
    gmail_app_password: str = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    imap_server: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    imap_port: int = int(os.getenv("IMAP_PORT", "993"))
    sync_interval_seconds: int = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
    fetch_limit: int = int(os.getenv("FETCH_LIMIT", "30"))
    
    student_name: str = os.getenv("STUDENT_NAME", "Shashwat Pratap Singh")
    student_roll: str = os.getenv("STUDENT_ROLL", "23BAI11174")
    student_neopat: str = os.getenv("STUDENT_NEOPAT", "S4Z5F7U9")
    student_degree: str = os.getenv("STUDENT_DEGREE", "B.Tech")
    student_branch: str = os.getenv("STUDENT_BRANCH", "CSE (AI & ML)")
    student_batch: int = int(os.getenv("STUDENT_BATCH", "2027"))
    student_10th: float = float(os.getenv("STUDENT_10TH", "72.6"))
    student_12th: float = float(os.getenv("STUDENT_12TH", "69.0"))
    student_cgpa: float = float(os.getenv("STUDENT_CGPA", "7.85"))
    student_arrears: int = int(os.getenv("STUDENT_STANDING_ARREARS", "0"))
    
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    whatsapp_api_url: str = os.getenv("WHATSAPP_API_URL", "")
    whatsapp_token: str = os.getenv("WHATSAPP_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    sound_alerts_enabled: bool = True
    default_sound: str = "urgent_ping"

settings = Settings()
