"""
Google Meet OAuth Authentication Wrapper.

Manages OAuth 2.0 flow, token caching (token.json), and scope validation:
- https://www.googleapis.com/auth/meetings.space.readonly
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("meetloop.tools.gmeet_auth")

SCOPES = ["https://www.googleapis.com/auth/meetings.space.readonly"]


def get_credentials(
    credentials_path: Optional[str] = None,
    token_path: Optional[str] = None,
    mock: bool = False,
):
    """
    Retrieves valid Google OAuth 2.0 credentials.
    Returns credentials object or None if running in mock/dry-run mode.
    """
    is_dry_run = (
        mock
        or os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    )
    
    if is_dry_run:
        logger.info("[DRY-RUN] Google Meet auth using simulated credentials.")
        return None

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        token_file = token_path or os.getenv("GOOGLE_TOKEN_PATH", "token.json")
        creds_file = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.path.exists(creds_file):
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, "w", encoding="utf-8") as token_out:
                    token_out.write(creds.to_json())
            else:
                logger.warning(
                    f"Google credentials file '{creds_file}' not found. Falling back to mock/dry-run mode."
                )
                return None

        return creds
    except Exception as e:
        logger.warning(f"Failed to load Google credentials: {e}. Falling back to dry-run mode.")
        return None
