"""
Google Meet Transcript Ingestion Node for MeetLoop.

If state contains `gmeet_meeting_code` or `gmeet_date_range`, fetches the real transcript
via Google Meet REST API and appends it to `raw_meeting_notes` / `raw_input`.
Short-circuits gracefully if no Google Meet input was provided (manual paste mode continues working).
"""

import os
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools.gmeet_auth import get_credentials
from backend.tools.gmeet_client import (
    list_conference_records,
    list_transcript_entries,
    build_transcript_text,
)
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("meetloop.agent.fetch_gmeet_transcript")


def fetch_gmeet_transcript_node(state: ClearRoomState) -> Dict[str, Any]:
    meeting_code = state.get("gmeet_meeting_code")
    date_range = state.get("gmeet_date_range")

    # If user chose manual paste, no-op cleanly
    if not meeting_code and not date_range:
        return {}

    print(f"[Node: fetch_gmeet_transcript] Fetching Google Meet transcript for code '{meeting_code}'...")

    creds = get_credentials()
    records = list_conference_records(creds, meeting_code=meeting_code)

    errors = list(state.get("errors") or [])

    if not records:
        logger.warning(f"No conference record found for Google Meet code '{meeting_code}'")
        errors.append({
            "node": "fetch_gmeet_transcript",
            "message": f"No conference record found for meeting code '{meeting_code}'. Check transcription was enabled during the meeting.",
        })
        new_trace = append_trace_step(
            existing_trace=state.get("reasoning_trace"),
            node_name="fetch_gmeet_transcript",
            what_it_decided=f"Google Meet transcript fetch skipped (no conference record found for '{meeting_code}')",
            input_summary=f"Query meeting_code='{meeting_code}'",
            output_summary="No records returned from Google Meet API",
            status="warning",
        )
        return {
            "gmeet_transcript_fetched": False,
            "errors": errors,
            "reasoning_trace": new_trace,
        }

    # Take the matching conference record
    record = records[0]
    entries = list_transcript_entries(creds, conference_record_name=record.get("name", "conferenceRecords/meet_01"))

    if not entries:
        logger.warning("Conference record found but transcript entries are empty.")
        errors.append({
            "node": "fetch_gmeet_transcript",
            "message": "Conference record found but transcript is empty. Transcription may not have been active.",
        })
        new_trace = append_trace_step(
            existing_trace=state.get("reasoning_trace"),
            node_name="fetch_gmeet_transcript",
            what_it_decided="Google Meet record found but transcript was empty",
            input_summary=f"Record: {record.get('name')}",
            output_summary="Empty transcript entries",
            status="warning",
        )
        return {
            "gmeet_transcript_fetched": False,
            "errors": errors,
            "reasoning_trace": new_trace,
        }

    transcript_text = build_transcript_text(entries)
    meeting_title = record.get("name", f"Google Meet {meeting_code}").split("/")[-1]
    tagged_transcript = f"Title: Google Meet ({meeting_code or meeting_title})\nDate: 2026-09-28\n\n{transcript_text}"

    # Append to raw_meeting_notes and raw_input
    existing_notes = list(state.get("raw_meeting_notes") or [])
    existing_notes.append(tagged_transcript)

    current_raw = state.get("raw_input") or ""
    combined_raw = f"{current_raw}\n\n{tagged_transcript}".strip() if current_raw else tagged_transcript

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="fetch_gmeet_transcript",
        what_it_decided=f"Pulled real transcript from Google Meet API ({len(entries)} spoken entries)",
        input_summary=f"Meeting code: '{meeting_code}', record: {record.get('name')}",
        output_summary=f"Assembled {len(entries)} transcript entries into clean meeting dialogue",
        tool_calls=[{"tool": "GoogleMeet", "action": "list_transcript_entries", "code": meeting_code}],
        status="success",
    )

    return {
        "raw_meeting_notes": existing_notes,
        "raw_input": combined_raw,
        "gmeet_transcript_fetched": True,
        "reasoning_trace": new_trace,
    }
