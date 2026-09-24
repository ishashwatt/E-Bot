import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import requests
from app.core.config import settings

logger = logging.getLogger("notifier")

class NotificationManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """
        Broadcasts real-time notification to all connected browser tabs with sound payload.
        """
        message_json = json.dumps(alert_data)
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                dead_connections.append(connection)
        
    def broadcast_alert_sync(self, alert_data: Dict[str, Any]):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast_alert(alert_data), loop)
            else:
                loop.run_until_complete(self.broadcast_alert(alert_data))
        except Exception:
            pass

    @staticmethod
    def send_telegram_alert(message_text: str, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
        """
        Sends free instant mobile notification to Telegram bot from .env.
        """
        token = bot_token or settings.telegram_bot_token
        chat = chat_id or settings.telegram_chat_id
        if not token or not chat:
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat,
                "text": message_text,
                "parse_mode": "HTML"
            }
            res = requests.post(url, json=payload, timeout=6)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    @staticmethod
    def send_whatsapp_alert(message_text: str) -> bool:
        """
        Sends mobile alert to WhatsApp Webhook / Gateway if configured in .env.
        """
        url = settings.whatsapp_api_url
        token = settings.whatsapp_token
        if not url:
            return False
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            payload = {"message": message_text}
            res = requests.post(url, json=payload, headers=headers, timeout=6)
            return res.status_code in [200, 201, 202]
        except Exception as e:
            logger.error(f"Failed to send WhatsApp alert: {e}")
            return False

notifier = NotificationManager()
