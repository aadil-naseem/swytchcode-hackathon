"""
Slack Client Wrapper for Swytchcode / Slack API integration.

Provides typed, robust functions to:
- post_message(channel_id, text_or_blocks) -> bool

Supports mock/dry-run mode for offline development and testing.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
import swytchcode_runtime

load_dotenv()

logger = logging.getLogger("meetloop.tools.slack")


class SlackClientError(Exception):
    """Base exception for Slack tool wrapper errors."""
    pass


class SlackAuthError(SlackClientError):
    """Raised when authentication with Slack/Swytchcode fails."""
    pass


class SlackPostError(SlackClientError):
    """Raised when posting a message to Slack fails."""
    pass


def _is_dry_run(explicit_mock: bool = False) -> bool:
    if explicit_mock:
        return True
    env_dry_run = os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
    env_mock = os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    api_key = os.getenv("SWYTCHCODE_API_KEY") or os.getenv("SLACK_API_KEY")
    return env_dry_run or env_mock or not api_key


def post_message(
    channel_id: Optional[str] = None,
    text_or_blocks: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None,
    mock: bool = False,
) -> bool:
    """
    Posts a message or block kit payload to the designated Slack channel.
    
    Returns True on success, or raises a SlackClientError.
    """
    channel_id = channel_id or os.getenv("SLACK_CHANNEL_ID", "C_MEETLOOP_ALERTS")
    dry_run = _is_dry_run(mock)

    if dry_run:
        text_preview = str(text_or_blocks)[:120] if text_or_blocks else "(empty)"
        logger.info(f"[DRY-RUN] Slack post_message channel='{channel_id}': {text_preview}...")
        return True

    payload: Dict[str, Any] = {"channel": channel_id}
    if isinstance(text_or_blocks, str):
        payload["text"] = text_or_blocks
    elif isinstance(text_or_blocks, list):
        payload["blocks"] = text_or_blocks
        payload["text"] = "MeetLoop Slack Pulse Update"
    elif isinstance(text_or_blocks, dict):
        if "blocks" in text_or_blocks:
            payload.update(text_or_blocks)
        else:
            payload["text"] = str(text_or_blocks)

    try:
        res = swytchcode_runtime.exec("slack.chat.postmessage.create", input={"body": payload})
        data = res.get("data", {}) if isinstance(res, dict) else {}
        if not data.get("ok", True):
            err = data.get("error", "unknown")
            if err == "not_in_channel":
                raise SlackPostError(
                    f"Slack error 'not_in_channel': The Swytchcode bot is not in channel '{channel_id}'. "
                    f"Fix: Go to that channel in Slack and type '/invite @<bot_name>' or add the app to the channel."
                )
            raise SlackPostError(f"Slack API error: {err}")
        logger.info(f"[LIVE] Slack message posted successfully to channel {channel_id}")
        return True
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg:
            raise SlackAuthError("Slack/Swytchcode authentication failed. Check credentials.") from e
        raise SlackClientError(f"Failed to post to Slack via Swytchcode: {err_msg}") from e
