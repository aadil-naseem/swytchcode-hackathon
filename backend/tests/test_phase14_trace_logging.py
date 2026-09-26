"""
Test script for Phase 14: Agent Reasoning / Audit Trail Logging Layer.
Verifies structured trace accumulation, tool call tracking, timestamps, and formatting.
"""

import os
import sys
import glob

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.graph import clearroom_agent
from backend.observability import format_trace_for_display


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def test_audit_mode_reasoning_trace():
    print("\n--- [1/3] Testing Audit Mode 8-Step Reasoning Trace & Tool Tracking ---")
    transcripts = load_all_fixtures()

    final_state = clearroom_agent.invoke({
        "mode": "audit",
        "raw_meeting_notes": transcripts,
        "reasoning_trace": [],
        "errors": [],
    })

    trace = final_state.get("reasoning_trace", [])
    assert len(trace) == 8, f"Expected exactly 8 trace steps, got {len(trace)}"

    print(f"Total Audit Trace Steps: {len(trace)}")
    for step in trace:
        print(f"  Step {step['step']}: [{step['node']}] -> {step['decision']} (Tools: {len(step.get('tool_calls', []))})")
        assert "timestamp" in step, f"Missing timestamp in step {step['step']}"
        assert "status" in step, f"Missing status in step {step['step']}"
        assert "input_summary" in step, f"Missing input_summary in step {step['step']}"
        assert "output_summary" in step, f"Missing output_summary in step {step['step']}"

    # Verify Swytchcode Tool Calls are recorded in trace
    tools_called = [tc["tool"] for s in trace for tc in s.get("tool_calls", [])]
    print(f"\nRecorded Tool Integrations in Audit Trace: {set(tools_called)}")
    assert "Notion" in tools_called, "Notion tool call not captured in trace!"
    assert "Gmail" in tools_called, "Gmail tool call not captured in trace!"
    assert "Slack" in tools_called, "Slack tool call not captured in trace!"

    print("  [PASS] Audit mode reasoning trace records all 8 steps and all 3 Swytchcode tools.")


def test_brief_mode_reasoning_trace():
    print("\n--- [2/3] Testing Brief Mode 4-Step Reasoning Trace & Tool Tracking ---")

    final_state = clearroom_agent.invoke({
        "prompt": "I have a meeting tomorrow about Pricing Strategy — brief me",
        "reasoning_trace": [],
        "errors": [],
    })

    trace = final_state.get("reasoning_trace", [])
    assert len(trace) == 4, f"Expected 4 trace steps, got {len(trace)}"

    print(f"Total Brief Trace Steps: {len(trace)}")
    for step in trace:
        print(f"  Step {step['step']}: [{step['node']}] -> {step['decision']} (Tools: {len(step.get('tool_calls', []))})")

    tools_called = [tc["tool"] for s in trace for tc in s.get("tool_calls", [])]
    print(f"Recorded Tool Integrations in Brief Trace: {set(tools_called)}")
    assert "Notion" in tools_called
    assert "Gmail" in tools_called

    print("  [PASS] Brief mode reasoning trace records all 4 steps and search tool calls.")


def test_trace_formatter():
    print("\n--- [3/3] Testing Human-Readable Trace Formatter ---")
    mock_trace = [
        {
            "step": 1,
            "node": "classify_input",
            "decision": "Routed to AUDIT mode",
            "output_summary": "Selected mode: audit",
            "status": "success",
            "tool_calls": [],
        },
        {
            "step": 2,
            "node": "write_notion_report",
            "decision": "Published Team Health Report to Notion",
            "output_summary": "Created Notion page -> https://notion.so/report-123",
            "status": "success",
            "tool_calls": [{"tool": "Notion", "action": "create_page"}],
        }
    ]
    formatted = format_trace_for_display(mock_trace)
    assert "=== ClearRoom Live Agent Reasoning Trace ===" in formatted
    assert "Notion (create_page)" in formatted
    print("  [PASS] Trace formatter generated clean display output.")


def main():
    print("==================================================")
    print(" Running Phase 14: Agent Reasoning Trace Tests    ")
    print("==================================================")
    try:
        test_audit_mode_reasoning_trace()
        test_brief_mode_reasoning_trace()
        test_trace_formatter()
        print("\n==================================================")
        print(" [ALL PHASE 14 TESTS PASSED] Trace Engine Ready!  ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
