"""
Test script for Phase 11: Audit Mode Gmail Digest.
Verifies manager digest email composition, Swytchcode tool execution, and soft-fail error handling.
"""

import os
import sys
import glob
from unittest.mock import patch

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.nodes.analyze_meetings import analyze_meetings_node
from backend.agent.nodes.extract_patterns import extract_patterns_node
from backend.agent.nodes.detect_stuck_topics import detect_stuck_topics_node
from backend.agent.nodes.write_notion_report import write_notion_report_node
from backend.agent.nodes.write_notion_decision_page import write_notion_decision_page_node
from backend.agent.nodes.send_gmail_digest import send_gmail_digest_node, _compose_gmail_digest_body


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def build_test_state():
    transcripts = load_all_fixtures()
    state = {"raw_meeting_notes": transcripts, "reasoning_trace": [], "errors": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))
    state.update(write_notion_report_node(state))
    state.update(write_notion_decision_page_node(state))
    return state


def test_gmail_body_composition():
    print("\n--- [1/3] Testing Gmail Digest Body Formatting ---")
    state = build_test_state()
    body = _compose_gmail_digest_body(state)

    print(f"Generated email body ({len(body)} characters)")

    assert "Pricing Strategy" in body, "Missing Pricing Strategy in email body!"
    assert "Arjun" in body and "OVERLOADED" in body, "Missing Overload alert in email body!"
    assert "Convert to async" in body or "Recommendation" in body, "Missing async recommendation!"
    assert state.get("notion_report_url") in body, "Missing Notion health report link in email!"

    print("  [PASS] Email body contains all required executive findings and links.")


def test_gmail_digest_send_success():
    print("\n--- [2/3] Testing send_gmail_digest_node Success Path ---")
    state = build_test_state()
    result = send_gmail_digest_node(state)

    assert result.get("gmail_digest_sent") is True, "gmail_digest_sent should be True on success"
    print("  [PASS] send_gmail_digest_node dispatched successfully.")

    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0
    print(f"  [PASS] Trace logged: {trace[-1]['output_summary']}")


def test_gmail_digest_soft_failure():
    print("\n--- [3/3] Testing send_gmail_digest_node Soft-Failure Graceful Handling ---")
    state = build_test_state()

    # Simulate Gmail API failure
    with patch("backend.agent.nodes.send_gmail_digest.gmail_send_email", side_effect=RuntimeError("Simulated SMTP/API failure")):
        result = send_gmail_digest_node(state)

    assert result.get("gmail_digest_sent") is False, "gmail_digest_sent should be False on error"
    errors = result.get("errors", [])
    assert len(errors) > 0, "Error should be recorded in state['errors']"
    assert errors[-1]["node"] == "send_gmail_digest"
    assert "Simulated SMTP/API failure" in errors[-1]["message"]

    print("  [PASS] Soft-failure caught and logged in state['errors'] without crashing graph!")


def main():
    print("==================================================")
    print(" Running Phase 11: Gmail Digest Tests             ")
    print("==================================================")
    try:
        test_gmail_body_composition()
        test_gmail_digest_send_success()
        test_gmail_digest_soft_failure()
        print("\n==================================================")
        print(" [ALL PHASE 11 TESTS PASSED] Gmail Digest Ready!  ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
