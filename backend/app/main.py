import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.db.database import engine, Base
from app.services.live_mail_sync import start_background_mail_sync
import uvicorn
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Bot - Real-time College Mail & Placement Intelligence",
    description="Real-time IMAP mailbox monitoring, PDF attachment deep-scanning, trailing thread tracking, and custom sound alerting system.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def app_startup():
    asyncio.create_task(start_background_mail_sync(interval_seconds=60))

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "E-Bot Live Intelligence Engine",
        "mode": "Live Mailbox Synchronization (IMAP / Google Workspace)"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
