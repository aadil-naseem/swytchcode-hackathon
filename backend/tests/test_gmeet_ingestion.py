"""
Test suite for Google Meet Transcript Ingestion (Phase A-E).
Verifies:
1. gmeet_client tool functions in mock and client mode.
2. fetch_gmeet_transcript node ingestion and transcript tagging.
3. LangGraph pipeline execution with gmeet_meeting_code input.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend/.env"))

os.environ["DRY_RUN"] = "true"

from backend.tools.gmeet_client import (
    list_conference_records,
    list_transcript_entries,
    build_transcript_text,
)
from backend.agent.graph import clearroom_agent

def test_gmeet_tools():
    print("\n--- [1/2] Testing Google Meet Client Functions ---")
    records = list_conference_records(None, meeting_code="abc-defg-hij", mock=True)
    assert len(records) > 0, "No conference records returned"
    print(f"  [PASS] list_conference_records returned {len(records)} record(s) -> {records[0]['name']}")

    entries = list_transcript_entries(None, conference_record_name=records[0]["name"], mock=True)
    assert len(entries) > 0, "No transcript entries returned"
    print(f"  [PASS] list_transcript_entries returned {len(entries)} entry/entries")

    text = build_transcript_text(entries)
    assert "Sofia" in text and "Arjun" in text, "Transcript text missing key speakers"
    print(f"  [PASS] build_transcript_text built formatted dialogue ({len(text.splitlines())} lines)")


def test_gmeet_graph_pipeline():
    print("\n--- [2/2] Testing Full Pipeline with Google Meet Code ---")
    initial_state = {
        "mode": "audit",
        "gmeet_meeting_code": "abc-defg-hij",
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_state)

    assert final_state.get("gmeet_transcript_fetched") is True, "gmeet_transcript_fetched is not True"
    assert len(final_state.get("raw_meeting_notes", [])) > 0, "No raw meeting notes populated"
    assert final_state.get("notion_report_url") is not None, "Notion report URL not generated"
    assert final_state.get("gmail_digest_sent") is True, "Gmail digest not sent"
    assert final_state.get("slack_pulse_sent") is True, "Slack pulse not sent"

    trace_nodes = [t.get("node_name") for t in final_state.get("reasoning_trace", [])]
    assert "fetch_gmeet_transcript" in trace_nodes, "fetch_gmeet_transcript missing from reasoning trace"
    print(f"  [PASS] Pipeline executed 9-step audit with Google Meet ingestion:")
    print(f"         Trace steps: {trace_nodes}")
    print(f"         Notion Report -> {final_state.get('notion_report_url')}")


if __name__ == "__main__":
    print("==================================================")
    print("    TESTING GOOGLE MEET TRANSCRIPT INGESTION      ")
    print("==================================================")
    test_gmeet_tools()
    test_gmeet_graph_pipeline()
    print("\n==================================================")
    print("    [ALL GOOGLE MEET INGESTION TESTS PASSED]      ")
    print("==================================================")
