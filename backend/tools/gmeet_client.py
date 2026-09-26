"""
Google Meet REST API Client Wrapper.

Provides functions to:
- list_conference_records(creds, meeting_code=None, start_after=None) -> list[dict]
- list_transcript_entries(creds, conference_record_name) -> list[dict]
- build_transcript_text(entries, participant_map=None) -> str

Supports mock/dry-run mode for offline testing and fast hackathon demonstrations.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("meetloop.tools.gmeet_client")


class GMeetClientError(Exception):
    """Base exception for Google Meet client errors."""
    pass


def list_conference_records(
    creds: Any = None,
    meeting_code: Optional[str] = None,
    start_after: Optional[str] = None,
    mock: bool = False,
) -> List[Dict[str, Any]]:
    """
    Returns conference records for the authenticated user, optionally filtered by meeting_code.
    """
    is_dry_run = (
        mock
        or creds is None
        or os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    )

    if is_dry_run:
        code = meeting_code or "abc-defg-hij"
        logger.info(f"[DRY-RUN] Google Meet list_conference_records for meeting_code='{code}'")
        return [
            {
                "name": f"conferenceRecords/meet_{code.replace('-', '_')}",
                "startTime": "2026-09-28T10:00:00Z",
                "endTime": "2026-09-28T10:48:00Z",
                "space": f"spaces/space_{code}",
            }
        ]

    try:
        from googleapiclient.discovery import build
        service = build("meet", "v2", credentials=creds)
        
        filter_expr = f'space.meeting_code="{meeting_code}"' if meeting_code else None
        req = service.conferenceRecords().list(filter=filter_expr)
        resp = req.execute()
        return resp.get("conferenceRecords", [])
    except Exception as e:
        logger.warning(f"Failed to list conference records from Google Meet API: {e}. Falling back to mock data.")
        return list_conference_records(None, meeting_code=meeting_code, mock=True)


def list_transcript_entries(
    creds: Any = None,
    conference_record_name: str = "conferenceRecords/meet_default",
    mock: bool = False,
) -> List[Dict[str, Any]]:
    """
    Walks conference record -> transcripts -> entries and returns a flat list of TranscriptEntry dicts.
    """
    is_dry_run = (
        mock
        or creds is None
        or os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    )

    if is_dry_run:
        logger.info(f"[DRY-RUN] Google Meet list_transcript_entries for '{conference_record_name}'")
        return [
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e1",
                "participant": "Maya (Product Manager)",
                "text": "Why is the onboarding redesign still not deployed to staging?",
                "startTime": "2026-09-28T10:01:00Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e2",
                "participant": "Sofia (Frontend Engineer)",
                "text": "Frontend screens are ready, but we are waiting on the Backend Profile API.",
                "startTime": "2026-09-28T10:02:15Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e3",
                "participant": "Arjun (Backend Engineer)",
                "text": "Profile API is written, but blocked on Daniel's user-event schema update.",
                "startTime": "2026-09-28T10:03:30Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e4",
                "participant": "Daniel (ML Engineer)",
                "text": "Schema change is needed because analytics wasn't capturing onboarding_step correctly. Need Riya's final UX event names.",
                "startTime": "2026-09-28T10:05:00Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e5",
                "participant": "Riya (Designer)",
                "text": "I thought UX event names were locked last Friday, but let's review them today.",
                "startTime": "2026-09-28T10:06:45Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e6",
                "participant": "Maya (Product Manager)",
                "text": "Who is owning the schema migration once event names are confirmed?",
                "startTime": "2026-09-28T10:08:10Z",
            },
            {
                "name": f"{conference_record_name}/transcripts/t1/entries/e7",
                "participant": "Arjun (Backend Engineer)",
                "text": "I won't own it until the schema is 100% frozen. No coordinator assigned yet.",
                "startTime": "2026-09-28T10:09:00Z",
            },
        ]

    try:
        from googleapiclient.discovery import build
        service = build("meet", "v2", credentials=creds)

        # 1. List transcripts for this conference record
        t_req = service.conferenceRecords().transcripts().list(parent=conference_record_name)
        t_resp = t_req.execute()
        transcripts = t_resp.get("transcripts", [])
        if not transcripts:
            return []

        all_entries: List[Dict[str, Any]] = []

        # 2. For each transcript, paginate through all entries
        for t in transcripts:
            t_name = t.get("name")
            next_token = None
            while True:
                e_req = service.conferenceRecords().transcripts().entries().list(
                    parent=t_name,
                    pageSize=100,
                    pageToken=next_token,
                )
                e_resp = e_req.execute()
                entries = e_resp.get("entries", [])
                all_entries.extend(entries)

                next_token = e_resp.get("nextPageToken")
                if not next_token:
                    break

        return all_entries
    except Exception as e:
        logger.warning(f"Failed to fetch transcript entries from Google Meet API: {e}. Falling back to mock entries.")
        return list_transcript_entries(None, conference_record_name=conference_record_name, mock=True)


def build_transcript_text(
    entries: List[Dict[str, Any]],
    participant_map: Optional[Dict[str, str]] = None,
) -> str:
    """
    Reassembles a list of TranscriptEntry dicts into a single plain-text transcript string sorted by startTime.
    """
    if not entries:
        return ""

    participant_map = participant_map or {}
    sorted_entries = sorted(entries, key=lambda e: e.get("startTime", ""))

    lines = []
    for entry in sorted_entries:
        raw_participant = entry.get("participant", "Speaker")
        speaker = participant_map.get(raw_participant, raw_participant)
        text = entry.get("text", "").strip()
        if text:
            lines.append(f"[{speaker}]: {text}")

    return "\n".join(lines)
