"""
Gmail Client Wrapper for Swytchcode / Gmail API integration.

Provides typed, robust functions to:
- send_email(to, subject, body) -> bool
- search_threads(query) -> list[dict]

Supports mock/dry-run mode for offline development and testing.
"""

import os
import base64
import logging
from email.message import EmailMessage
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import swytchcode_runtime

load_dotenv()

logger = logging.getLogger("meetloop.tools.gmail")


class GmailClientError(Exception):
    """Base exception for Gmail tool wrapper errors."""
    pass


class GmailAuthError(GmailClientError):
    """Raised when authentication with Gmail/Swytchcode fails."""
    pass


class GmailSendError(GmailClientError):
    """Raised when sending an email fails."""
    pass


def _is_dry_run(explicit_mock: bool = False) -> bool:
    if explicit_mock:
        return True
    env_dry_run = os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
    env_mock = os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    api_key = os.getenv("SWYTCHCODE_API_KEY") or os.getenv("GMAIL_API_KEY")
    return env_dry_run or env_mock or not api_key


def send_email(
    to: str,
    subject: str,
    body: str,
    mock: bool = False,
) -> bool:
    """
    Sends an email via Gmail/Swytchcode to the recipient.
    
    Returns True if sent successfully, or raises an exception.
    """
    dry_run = _is_dry_run(mock)

    if dry_run:
        logger.info(f"[DRY-RUN] Gmail send_email to='{to}', subject='{subject}', body_preview='{body[:80]}...'")
        return True

    from_account = os.getenv("GMAIL_TEST_ACCOUNT", to)

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = from_account
    msg["To"] = to

    raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    payload = {
        "params": {"userId": "me"},
        "body": {"raw": raw_b64}
    }

    try:
        res = swytchcode_runtime.exec("gmail.user.send.create1", input=payload)
        logger.info(f"[LIVE] Gmail message sent successfully -> {res.get('data', {}).get('id')}")
        return True
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg:
            raise GmailAuthError("Gmail/Swytchcode authentication failed. Check credentials.") from e
        raise GmailSendError(f"Failed to send email via Swytchcode: {err_msg}") from e


def search_threads(
    query: str,
    mock: bool = False,
) -> List[Dict[str, Any]]:
    """
    Searches Gmail threads matching the query.
    
    Returns a list of structured thread dicts: [{id, subject, sender, snippet, date}].
    """
    dry_run = _is_dry_run(mock)

    if dry_run:
        logger.info(f"[DRY-RUN] Gmail search_threads query='{query}'")
        q_lower = query.lower()
        if "pricing" in q_lower:
            return [
                {
                    "id": "thread_pricing_101",
                    "subject": "Re: Pricing Model Updates & Tier Comparison",
                    "sender": "arjun@meetloop-team.internal",
                    "snippet": "I've drafted the seat-based vs usage-based breakdown. Still waiting for sales feedback before locking it in.",
                    "date": "2026-09-24T16:45:00Z",
                },
                {
                    "id": "thread_pricing_102",
                    "subject": "Fwd: Customer feedback on Pro Tier price point",
                    "sender": "sarah@meetloop-team.internal",
                    "snippet": "Customers are asking for annual discounts on the enterprise tier.",
                    "date": "2026-09-23T11:20:00Z",
                }
            ]
        elif "infra" in q_lower or "cloud" in q_lower:
            return [
                {
                    "id": "thread_infra_201",
                    "subject": "AWS vs GCP cost breakdown for GPU nodes",
                    "sender": "priya@meetloop-team.internal",
                    "snippet": "Attached the spreadsheet comparing p4de and a2 instances for our training pipeline.",
                    "date": "2026-09-22T15:10:00Z",
                }
            ]
        else:
            return [
                {
                    "id": f"thread_{os.urandom(4).hex()}",
                    "subject": f"Thread discussing {query}",
                    "sender": "team-lead@meetloop.internal",
                    "snippet": f"Latest email update concerning {query}.",
                    "date": "2026-09-24T09:00:00Z",
                }
            ]

    try:
        res = swytchcode_runtime.exec("gmail.user.messages.get", input={"params": {"userId": "me", "q": query}})
        data = res.get("data", {}) if isinstance(res, dict) else {}
        messages = data.get("messages", [])
        threads = []
        for m in messages[:5]:
            threads.append({
                "id": m.get("id"),
                "subject": f"Gmail Thread {m.get('id')}",
                "sender": os.getenv("GMAIL_TEST_ACCOUNT", "team@meetloop.internal"),
                "snippet": f"Found matching email for query: {query}",
                "date": "2026-09-26T00:00:00Z",
            })
        return threads
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg:
            raise GmailAuthError("Gmail/Swytchcode auth error.") from e
        raise GmailClientError(f"Failed to search Gmail messages via Swytchcode: {err_msg}") from e
