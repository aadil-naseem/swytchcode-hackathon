"""
MeetLoop Tool Wrapper Layer for Notion, Gmail, Slack, and Google Meet.
"""

from .notion_client import (
    create_page as notion_create_page,
    search_pages as notion_search_pages,
    read_page as notion_read_page,
    NotionClientError,
    NotionAuthError,
    NotionPageNotFoundError,
)

from .gmail_client import (
    send_email as gmail_send_email,
    search_threads as gmail_search_threads,
    GmailClientError,
    GmailAuthError,
    GmailSendError,
)

from .slack_client import (
    post_message as slack_post_message,
    SlackClientError,
    SlackAuthError,
    SlackPostError,
)

from .gmeet_client import (
    list_conference_records as gmeet_list_conference_records,
    list_transcript_entries as gmeet_list_transcript_entries,
    build_transcript_text as gmeet_build_transcript_text,
    GMeetClientError,
)
from .gmeet_auth import get_credentials as gmeet_get_credentials

__all__ = [
    "notion_create_page",
    "notion_search_pages",
    "notion_read_page",
    "NotionClientError",
    "NotionAuthError",
    "NotionPageNotFoundError",
    "gmail_send_email",
    "gmail_search_threads",
    "GmailClientError",
    "GmailAuthError",
    "GmailSendError",
    "slack_post_message",
    "SlackClientError",
    "SlackAuthError",
    "SlackPostError",
    "gmeet_list_conference_records",
    "gmeet_list_transcript_entries",
    "gmeet_build_transcript_text",
    "gmeet_get_credentials",
    "GMeetClientError",
]
