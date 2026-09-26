"""
Test script for Phase 10: Stuck Topic Notion Decision Pages.
Verifies decision page content block structure, Notion tool wrapper calls, and state url accumulation.
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
from backend.agent.nodes.write_notion_report import write_notion_report_node
from backend.agent.nodes.write_notion_decision_page import (
    write_notion_decision_page_node,
    _build_decision_page_blocks,
)


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def test_decision_page_block_structure():
    print("\n--- [1/2] Testing Decision Page Content Blocks ---")
    transcripts = load_all_fixtures()

    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))
    state.update(write_notion_report_node(state))

    stuck_topics = state.get("stuck_topics", [])
    assert len(stuck_topics) > 0, "No stuck topics found!"

    first_stuck = stuck_topics[0]
    blocks = _build_decision_page_blocks(first_stuck, state.get("notion_report_url", ""))
    full_text = "\n".join(blocks)

    print(f"Generated {len(blocks)} blocks for '{first_stuck.get('topic')}' ({len(full_text)} characters).")

    # Assert critical sections
    assert "Decision Framework" in full_text, "Missing Decision Framework title!"
    assert "What Is Blocking a Decision?" in full_text, "Missing Blocker section!"
    assert "Competing Stakeholder Perspectives" in full_text, "Missing Competing Views section!"
    assert "Historical Discussion Log" in full_text or "Historical Meetings" in full_text, "Missing Evidence log!"
    assert "Recommended Action Plan" in full_text, "Missing Action Plan section!"
    assert "@Arjun" in full_text, "Missing suggested owner tag!"
    assert first_stuck.get("blocking_reason") in full_text, "Missing root blocker content!"

    print("  [PASS] Notion Decision Page contains all structured executive sections.")


def test_write_notion_decision_page_node_execution():
    print("\n--- [2/2] Testing write_notion_decision_page_node Execution ---")
    transcripts = load_all_fixtures()

    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))
    state.update(write_notion_report_node(state))

    result = write_notion_decision_page_node(state)
    urls = result.get("notion_decision_page_urls", [])

    assert len(urls) > 0, "No decision page URLs returned!"
    for u in urls:
        assert u.startswith("https://notion.so/"), f"Invalid Decision Page URL: {u}"
        print(f"  [PASS] Created Decision Page -> {u}")

    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0
    print(f"  [PASS] Trace logged: {trace[-1]['output_summary']}")


def main():
    print("==================================================")
    print(" Running Phase 10: Notion Decision Page Tests     ")
    print("==================================================")
    try:
        test_decision_page_block_structure()
        test_write_notion_decision_page_node_execution()
        print("\n==================================================")
        print(" [ALL PHASE 10 TESTS PASSED] Decision Pages Ready!")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
