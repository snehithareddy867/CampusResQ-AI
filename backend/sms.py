"""Twilio SMS sender with graceful fallback when creds are missing."""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TWILIO_SID = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_FROM = os.environ.get("TWILIO_FROM", "").strip()


def sms_configured() -> bool:
    return bool(TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM)


async def send_sms(*, to: str, body: str) -> Optional[str]:
    """Send an SMS via Twilio. Returns message SID on success, None otherwise.
    Silently returns None if Twilio isn't configured (gate the call in emailer fallback)."""
    if not sms_configured():
        logger.info("SMS skipped (Twilio not configured)")
        return None
    if not to or not to.strip():
        return None
    try:
        import asyncio
        from twilio.rest import Client
        def _send():
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            msg = client.messages.create(body=body[:1500], from_=TWILIO_FROM, to=to.strip())
            return msg.sid
        return await asyncio.to_thread(_send)
    except Exception as e:
        logger.error(f"Twilio SMS failed: {e}")
        return None
