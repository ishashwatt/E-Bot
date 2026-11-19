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
        Includes robust retry: if Telegram rejects HTML entities (HTTP 400),
        it strips formatting and delivers the message in plain text.
        """
        token = bot_token or settings.telegram_bot_token
        chat = chat_id or settings.telegram_chat_id
        if not token or not chat or not message_text:
            return False

        import re

        # Telegram limit is 4096 characters
        truncated_msg = message_text if len(message_text) <= 4000 else message_text[:3950] + "\n\n...[Truncated]"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            # 1. First attempt: HTML formatted message
            payload = {
                "chat_id": chat,
                "text": truncated_msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            res = requests.post(url, json=payload, timeout=12)
            if res.status_code == 200:
                return True

            logger.warning(f"Telegram HTML send returned status {res.status_code}: {res.text}. Falling back to plain text.")

            # 2. Fallback: Strip HTML tags and send plain text
            plain_text = re.sub(r'<[^>]+>', '', truncated_msg)
            plain_payload = {
                "chat_id": chat,
                "text": plain_text,
                "disable_web_page_preview": True
            }
            res_plain = requests.post(url, json=plain_payload, timeout=12)
            if res_plain.status_code == 200:
                return True
            else:
                logger.error(f"Telegram plain text send failed {res_plain.status_code}: {res_plain.text}")
                return False
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
