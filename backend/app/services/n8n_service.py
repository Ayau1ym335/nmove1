"""app/services/n8n_service.py

n8n has been removed from the NMove stack.
This module is kept as a no-op stub so that any existing call-sites
(process_session task) continue to compile and run without modification.
The fire-and-forget function simply returns immediately; no HTTP calls
are made and no errors are raised.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def trigger_webhook_fire_and_forget(endpoint: str, payload: dict[str, Any]) -> None:
    """No-op stub: n8n service has been removed from the stack."""
    logger.debug(
        "n8n webhook '%s' skipped — n8n service is not running (removed from stack)",
        endpoint,
    )
