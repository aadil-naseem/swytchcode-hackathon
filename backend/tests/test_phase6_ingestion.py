"""
Test script for Phase 6: Audit Mode Data Ingestion & Preprocessing.
Loads fixtures from backend/tests/fixtures/ and verifies normalization into parsed_meetings.
"""

import os
import sys
import glob

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.nodes.analyze_meetings import analyze_meetings_node


def load_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts, fixture_files


def test_list_input_preprocessing():
    print("\n" + "=" * 50)
    print(" [TEST 1] Ingesting List of 4 Meeting Transcripts")
    print("=" * 50)

    transcripts, fixture_files = load_fixtures()
    assert len(transcripts) == 4, f"Expected 4 fixture files, found {len(transcripts)}"
    print(f"Loaded {len(transcripts)} fixture files from tests/fixtures/")

    initial_state = {
        "mode": "audit",
        "raw_meeting_notes": transcripts,
        "reasoning_trace": [],
    }

    result = analyze_meetings_node(initial_state)
    parsed = result.get("parsed_meetings", [])

    assert len(parsed) == 4, f"Expected 4 parsed meetings, got {len(parsed)}"

    # Verify Meeting 1
    m1 = parsed[0]
    print(f"\nMeeting 1: '{m1['title']}' | Date: {m1['date']} | Participants: {m1['participants']}")
    assert "Tuesday" in m1["title"]
    assert m1["date"] == "2026-09-22"
    assert "Arjun" in m1["participants"] and "Sarah" in m1["participants"]
    assert "[00:01:00]" not in m1["clean_transcript"], "Timestamps were not stripped!"

    # Verify Meeting 4 (Retrospective)
    m4 = parsed[3]
    print(f"Meeting 4: '{m4['title']}' | Date: {m4['date']} | Participants: {m4['participants']}")
    assert "Retrospective" in m4["title"]
    assert m4["date"] == "2026-09-25"

    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0
    print(f"\nTrace output: {trace[0]['output_summary']}")
    print("\n[PASS] List input preprocessing verified!")


def test_concatenated_string_input():
    print("\n" + "=" * 50)
    print(" [TEST 2] Ingesting Single Concatenated String with Delimiters")
    print("=" * 50)

    transcripts, _ = load_fixtures()
    concatenated = "\n\n---\n\n".join(transcripts)

    initial_state = {
        "mode": "audit",
        "raw_meeting_notes": [concatenated],
        "reasoning_trace": [],
    }

    result = analyze_meetings_node(initial_state)
    parsed = result.get("parsed_meetings", [])

    assert len(parsed) == 4, f"Expected delimiter split into 4 meetings, got {len(parsed)}"
    print(f"Successfully split delimited string into {len(parsed)} meetings.")
    print("\n[PASS] Concatenated string delimiter splitting verified!")


def main():
    try:
        test_list_input_preprocessing()
        test_concatenated_string_input()
        print("\n" + "=" * 50)
        print(" [ALL PHASE 6 TESTS PASSED] Ingestion & Preprocessing Ready! ")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
