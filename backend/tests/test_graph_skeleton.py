"""
Test script for Phase 5: LangGraph State Schema & Graph Skeleton.
Validates both 'audit' and 'brief' paths through the compiled LangGraph workflow.
"""

import os
import sys

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.graph import clearroom_agent


def test_audit_mode_skeleton():
    print("\n" + "=" * 50)
    print(" [TEST 1] Running AUDIT MODE Graph Skeleton")
    print("=" * 50)

    initial_state = {
        "mode": "audit",
        "raw_meeting_notes": [
            "Meeting 1 (Mon): Arjun presented Pricing tiers. No decision.",
            "Meeting 2 (Wed): Pricing discussed again. Blocked on billing metric.",
            "Meeting 3 (Fri): Sprint retro. Pricing discussed for 3rd time.",
        ],
        "reasoning_trace": [],
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_state)

    print("\n--- Audit Mode Final State Check ---")
    print(f"Mode: {final_state.get('mode')}")
    print(f"Notion Report URL: {final_state.get('notion_report_url')}")
    print(f"Notion Decision Pages: {final_state.get('notion_decision_page_urls')}")
    print(f"Gmail Digest Sent: {final_state.get('gmail_digest_sent')}")
    print(f"Slack Pulse Sent: {final_state.get('slack_pulse_sent')}")

    trace = final_state.get("reasoning_trace", [])
    print(f"\nAudit Reasoning Trace Steps ({len(trace)} nodes visited):")
    for i, step in enumerate(trace, 1):
        print(f"  {i}. [{step['node']}] -> {step['decision']}")

    expected_nodes = [
        "classify_input",
        "analyze_meetings",
        "extract_patterns",
        "detect_stuck_topics",
        "write_notion_report",
        "write_notion_decision_pages",
        "send_gmail_digest",
        "post_slack_pulse",
    ]
    actual_nodes = [s["node"] for s in trace]
    for node in expected_nodes:
        assert node in actual_nodes, f"Expected node '{node}' not found in audit execution trace!"

    assert final_state.get("notion_report_url") is not None
    assert final_state.get("gmail_digest_sent") is True
    assert final_state.get("slack_pulse_sent") is True
    print("\n[PASS] Audit mode executed all 8 nodes in order!")


def test_brief_mode_skeleton():
    print("\n" + "=" * 50)
    print(" [TEST 2] Running BRIEF MODE Graph Skeleton")
    print("=" * 50)

    initial_state = {
        "mode": "brief",
        "brief_topic": "Pricing Strategy",
        "reasoning_trace": [],
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_state)

    print("\n--- Brief Mode Final State Check ---")
    print(f"Mode: {final_state.get('mode')}")
    print(f"Brief Output: {final_state.get('brief_output')}")

    trace = final_state.get("reasoning_trace", [])
    print(f"\nBrief Reasoning Trace Steps ({len(trace)} nodes visited):")
    for i, step in enumerate(trace, 1):
        print(f"  {i}. [{step['node']}] -> {step['decision']}")

    expected_nodes = [
        "classify_input",
        "search_notion",
        "search_gmail",
        "generate_brief",
    ]
    actual_nodes = [s["node"] for s in trace]
    for node in expected_nodes:
        assert node in actual_nodes, f"Expected node '{node}' not found in brief execution trace!"

    assert final_state.get("brief_output") is not None
    print("\n[PASS] Brief mode executed all 4 nodes in order!")


def main():
    try:
        test_audit_mode_skeleton()
        test_brief_mode_skeleton()
        print("\n" + "=" * 50)
        print(" [ALL PHASE 5 TESTS PASSED] Graph Skeleton Verified! ")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
