import asyncio
import logging
from typing import Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

async def _send_webhook_async(endpoint: str, payload: dict[str, Any]) -> None:
    # URL construction bounds mapped to internal docker network resolver if missing
    url = f"http://nmove_n8n:5678/webhook/{endpoint}"
    
    try:
        # Strict timeout to guarantee we never block caller on network stall
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            logger.info(f"n8n webhook {endpoint} triggered successfully")
    except httpx.TimeoutException:
        logger.warning(f"n8n webhook {endpoint} timed out.")
    except Exception as e:
        logger.error(f"Failed to trigger n8n webhook {endpoint}: {e}")

def trigger_webhook_fire_and_forget(endpoint: str, payload: dict[str, Any]) -> None:
    """
    Triggers an n8n webhook in an isolated background asyncio task.
    This guarantees it's fire-and-forget and does not await resolution.
    It will gracefully time out and drop without mutating caller state.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send_webhook_async(endpoint, payload))
    except RuntimeError:
        # Fallback if no event loop running securely
        asyncio.run(_send_webhook_async(endpoint, payload))
