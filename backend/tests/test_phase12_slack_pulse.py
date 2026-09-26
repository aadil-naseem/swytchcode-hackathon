"""
Test script for Phase 12: Audit Mode Slack Weekly Pulse.
Verifies Slack pulse message composition, Swytchcode tool execution, soft-fail handling,
and runs the full end-to-end Audit Mode pipeline.
"""

import os
import sys
import glob
from unittest.mock import patch

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.graph import clearroom_agent
from backend.agent.nodes.analyze_meetings import analyze_meetings_node
from backend.agent.nodes.extract_patterns import extract_patterns_node
from backend.agent.nodes.detect_stuck_topics import detect_stuck_topics_node
from backend.agent.nodes.write_notion_report import write_notion_report_node
from backend.agent.nodes.write_notion_decision_page import write_notion_decision_page_node
from backend.agent.nodes.send_gmail_digest import send_gmail_digest_node
from backend.agent.nodes.post_slack_pulse import post_slack_pulse_node, _compose_slack_pulse_message


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
    state.update(send_gmail_digest_node(state))
    return state


def test_slack_pulse_message_composition():
    print("\n--- [1/4] Testing Slack Pulse Message Formatting ---")
    state = build_test_state()
    pulse = _compose_slack_pulse_message(state)

    print(f"Generated Slack Pulse ({len(pulse)} chars)")

    assert "Pricing Strategy" in pulse, "Missing Pricing Strategy in Slack message!"
    assert "Arjun" in pulse and "Workload Alert" in pulse, "Missing Workload Alert in Slack message!"
    assert "Convert to Async" in pulse or "Calendar Optimization" in pulse, "Missing Calendar Optimization in Slack message!"
    assert state.get("notion_report_url") in pulse, "Missing Notion report URL in Slack message!"

    print("  [PASS] Slack pulse message contains all structured bullet points and links.")


def test_slack_pulse_send_success():
    print("\n--- [2/4] Testing post_slack_pulse_node Success Path ---")
    state = build_test_state()
    result = post_slack_pulse_node(state)

    assert result.get("slack_pulse_sent") is True, "slack_pulse_sent should be True on success"
    print("  [PASS] post_slack_pulse_node posted successfully.")

    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0
    print(f"  [PASS] Trace logged: {trace[-1]['output_summary']}")


def test_slack_pulse_soft_failure():
    print("\n--- [3/4] Testing post_slack_pulse_node Soft-Failure Graceful Handling ---")
    state = build_test_state()

    with patch("backend.agent.nodes.post_slack_pulse.slack_post_message", side_effect=RuntimeError("Simulated Slack API rate limit")):
        result = post_slack_pulse_node(state)

    assert result.get("slack_pulse_sent") is False, "slack_pulse_sent should be False on error"
    errors = result.get("errors", [])
    assert len(errors) > 0, "Error should be recorded in state['errors']"
    assert errors[-1]["node"] == "post_slack_pulse"
    assert "Simulated Slack API rate limit" in errors[-1]["message"]

    print("  [PASS] Soft-failure caught and logged in state['errors'] without crashing!")


def test_full_audit_mode_pipeline():
    print("\n--- [4/4] PRIORITY CHECKPOINT: Full Audit Mode End-to-End Test ---")
    transcripts = load_all_fixtures()

    initial_input = {
        "mode": "audit",
        "raw_meeting_notes": transcripts,
        "reasoning_trace": [],
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_input)

    # 1. State verification
    assert final_state.get("mode") == "audit"
    assert len(final_state.get("parsed_meetings", [])) == 4
    assert len(final_state.get("stuck_topics", [])) > 0
    assert final_state.get("notion_report_url") is not None
    assert len(final_state.get("notion_decision_page_urls", [])) > 0
    assert final_state.get("gmail_digest_sent") is True
    assert final_state.get("slack_pulse_sent") is True

    print("\n=== AUDIT MODE EXECUTION RESULTS ===")
    print(f"  • Parsed Meetings: {len(final_state['parsed_meetings'])}")
    print(f"  • Stuck Topic: '{final_state['stuck_topics'][0]['topic']}'")
    print(f"  • Notion Health Report URL: {final_state['notion_report_url']}")
    print(f"  • Notion Decision Page URL: {final_state['notion_decision_page_urls'][0]}")
    print(f"  • Gmail Digest Sent: {final_state['gmail_digest_sent']}")
    print(f"  • Slack Pulse Sent: {final_state['slack_pulse_sent']}")

    trace = final_state.get("reasoning_trace", [])
    print(f"\nExecution Trace ({len(trace)} steps):")
    for i, t in enumerate(trace, 1):
        print(f"  {i}. [{t['node']}] -> {t['decision']}")

    print("\n[PASS] Core Audit Mode fully functional end to end!")


def main():
    print("==================================================")
    print(" Running Phase 12: Slack Pulse & Audit E2E Tests  ")
    print("==================================================")
    try:
        test_slack_pulse_message_composition()
        test_slack_pulse_send_success()
        test_slack_pulse_soft_failure()
        test_full_audit_mode_pipeline()
        print("\n==================================================")
        print(" [ALL PHASE 12 TESTS PASSED] Audit Mode Complete! ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
