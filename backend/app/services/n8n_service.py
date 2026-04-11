"""app/services/n8n_service.py — Best-effort webhook notifier for n8n."""
import logging
import os
import threading
from typing import Any

import httpx

logger = logging.getLogger("nmove.n8n")


def _post_webhook(url: str, body: dict[str, Any]) -> None:
    """Send webhook payload in a background thread, never raising to callers."""
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(url, json=body)
    except Exception:
        logger.exception("n8n webhook delivery failed")


def trigger_webhook_fire_and_forget(event: str, payload: dict[str, Any]) -> None:
    """Trigger n8n webhook asynchronously without blocking application flow.

    Configure URL via `N8N_WEBHOOK_URL` (preferred) or `N8N_WEBHOOK_SESSION_URL`.
    If no URL is configured, the call is intentionally a no-op.
    """
    webhook_url = os.getenv("N8N_WEBHOOK_URL") or os.getenv("N8N_WEBHOOK_SESSION_URL")
    if not webhook_url:
        return

    body = {"event": event, "payload": payload}
    thread = threading.Thread(target=_post_webhook, args=(webhook_url, body), daemon=True)
    thread.start()
