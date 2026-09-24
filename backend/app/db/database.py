from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sqlite3
import logging

logger = logging.getLogger("database")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ebot.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def run_migrations():
    """
    Ensures that existing SQLite databases are automatically updated with any new columns.
    """
    try:
        if not os.path.exists(DB_PATH):
            return
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check email_messages columns
        cursor.execute("PRAGMA table_info(email_messages)")
        existing_cols = [c[1] for c in cursor.fetchall()]
        
        if existing_cols:
            columns_to_add = [
                ("priority", "TEXT DEFAULT 'Low'"),
                ("category", "TEXT DEFAULT 'General Circular'"),
                ("company_name", "TEXT"),
                ("venues", "JSON DEFAULT '[]'"),
                ("slots", "JSON DEFAULT '[]'"),
                ("action_links", "JSON DEFAULT '[]'"),
                ("deadline_date_time", "TEXT"),
                ("schedule_date_time", "TEXT"),
                ("reason", "TEXT DEFAULT ''"),
                ("plain_english_summary", "TEXT DEFAULT ''"),
            ]
            for col_name, col_def in columns_to_add:
                if col_name not in existing_cols:
                    try:
                        cursor.execute(f"ALTER TABLE email_messages ADD COLUMN {col_name} {col_def}")
                        conn.commit()
                        logger.info(f"Added column {col_name} to email_messages")
                    except Exception as ex:
                        logger.warning(f"Could not add column {col_name}: {ex}")
        conn.close()
    except Exception as e:
        logger.error(f"Migration error: {e}")

# Run migrations at import time
run_migrations()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
