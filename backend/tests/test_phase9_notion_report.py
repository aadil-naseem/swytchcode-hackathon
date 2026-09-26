"""
Test script for Phase 9: Notion Team Health Report.
Verifies report block formatting, Notion tool wrapper integration, and state url population.
"""

import os
import sys
import glob

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.nodes.analyze_meetings import analyze_meetings_node
from backend.agent.nodes.extract_patterns import extract_patterns_node
from backend.agent.nodes.detect_stuck_topics import detect_stuck_topics_node
from backend.agent.nodes.write_notion_report import write_notion_report_node, _build_notion_report_blocks


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def test_notion_health_report_generation():
    print("\n--- [1/2] Testing Notion Report Content Formatting ---")
    transcripts = load_all_fixtures()

    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))

    blocks = _build_notion_report_blocks(state)
    full_report_text = "\n".join(blocks)

    print(f"Generated {len(blocks)} report blocks ({len(full_report_text)} characters).")

    # Assert all key sections exist
    assert "Stuck Topics" in full_report_text, "Missing Stuck Topics section!"
    assert "Pricing Strategy" in full_report_text, "Missing Pricing Strategy stuck topic!"
    assert "Commitment Load" in full_report_text, "Missing Commitment Load section!"
    assert "Arjun" in full_report_text and "7 action items" in full_report_text, "Missing overloaded Arjun breakdown!"
    assert "Meeting Type Efficiency" in full_report_text, "Missing Meeting Type Efficiency section!"
    assert "Daily Standup" in full_report_text and "Convert to Async" in full_report_text, "Missing async recommendation!"

    print("  [PASS] All 4 executive report sections formatted properly.")


def test_write_notion_report_node_execution():
    print("\n--- [2/2] Testing write_notion_report_node Execution ---")
    transcripts = load_all_fixtures()

    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))
    result = write_notion_report_node(state)

    report_url = result.get("notion_report_url")
    assert report_url is not None, "notion_report_url was not returned!"
    assert report_url.startswith("https://notion.so/"), f"Invalid Notion URL: {report_url}"

    print(f"  [PASS] Successfully generated Notion report URL -> {report_url}")

    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0
    print(f"  [PASS] Trace logged: {trace[-1]['output_summary']}")


def main():
    print("==================================================")
    print(" Running Phase 9: Notion Team Health Report Tests ")
    print("==================================================")
    try:
        test_notion_health_report_generation()
        test_write_notion_report_node_execution()
        print("\n==================================================")
        print(" [ALL PHASE 9 TESTS PASSED] Health Report Ready!  ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
