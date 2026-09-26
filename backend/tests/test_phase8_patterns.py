"""
Test script for Phase 8: Pattern Extraction & Stuck Topic Detection.
Verifies ranking, blocker synthesis, owner suggestion, and evidence collation.
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
from backend.agent.nodes.detect_stuck_topics import detect_stuck_topics_node, PROMPT_PATH


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def test_prompt_file():
    print("\n--- [1/3] Checking Stuck Topic Prompt ---")
    assert os.path.exists(PROMPT_PATH), f"Prompt not found at {PROMPT_PATH}"
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "blocking_reason" in content
    assert "suggested_owner" in content
    assert "suggested_next_step" in content
    print(f"  [PASS] Stuck topic prompt exists with synthesis schema ({len(content)} chars).")


def test_pattern_extraction_and_stuck_topics():
    print("\n--- [2/3] Testing extract_patterns & detect_stuck_topics Nodes ---")
    transcripts = load_all_fixtures()

    # Step 1: Ingest & Analyze
    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))

    # Step 2: Extract Patterns
    state.update(extract_patterns_node(state))

    # Verify Commitment Load ranking
    comm = state.get("commitment_load", {})
    ranked_team = comm.get("ranked_team", [])
    assert len(ranked_team) > 0, "Missing ranked team commitment load!"
    top_person = ranked_team[0]
    print(f"  [PASS] Top Commitment Load: {top_person['name']} with {top_person['action_item_count']} items ({top_person['percentage_of_all_tasks']}%)")
    assert top_person["name"] == "Arjun"
    assert top_person["is_overloaded"] is True

    # Verify Meeting Type efficiency ranking
    ranked_meetings = state.get("meeting_necessity_scores", {}).get("ranked_categories", [])
    assert len(ranked_meetings) > 0, "Missing ranked meeting types!"
    least_efficient = ranked_meetings[0]
    print(f"  [PASS] Lowest Efficiency Meeting Type: '{least_efficient['category']}' -> Resolution Rate: {least_efficient['resolution_rate']*100:.0f}% -> Recommendation: '{least_efficient['async_recommendation']}'")
    assert least_efficient["resolution_rate"] == 0.0
    assert "Async" in least_efficient["async_recommendation"]

    # Step 3: Detect & Synthesize Stuck Topics
    state.update(detect_stuck_topics_node(state))

    stuck_list = state.get("stuck_topics", [])
    assert len(stuck_list) > 0, "state['stuck_topics'] is empty!"
    stuck_item = stuck_list[0]

    print(f"\n--- Synthesized Stuck Topic Profile ---")
    print(f"  • Topic: {stuck_item.get('topic')}")
    print(f"  • Occurrences: {stuck_item.get('occurrences')} meetings")
    print(f"  • Blocking Reason: {stuck_item.get('blocking_reason')}")
    print(f"  • Suggested Owner: {stuck_item.get('suggested_owner')}")
    print(f"  • Suggested Next Step: {stuck_item.get('suggested_next_step')}")
    print(f"  • Evidence Items Collected: {len(stuck_item.get('evidence', []))}")

    assert "Pricing" in stuck_item.get("topic")
    assert stuck_item.get("occurrences") >= 2
    assert stuck_item.get("blocking_reason") is not None and len(stuck_item.get("blocking_reason")) > 10
    assert stuck_item.get("suggested_owner") == "Arjun"
    assert len(stuck_item.get("suggested_next_step")) > 10
    assert len(stuck_item.get("evidence", [])) > 0

    print("\n[PASS] state['stuck_topics'] fully verified and ready for Notion Decision Pages!")


def test_trace_chain():
    print("\n--- [3/3] Checking Reasoning Trace Continuity ---")
    transcripts = load_all_fixtures()
    state = {"raw_meeting_notes": transcripts, "reasoning_trace": []}
    state.update(analyze_meetings_node(state))
    state.update(extract_patterns_node(state))
    state.update(detect_stuck_topics_node(state))

    trace = state.get("reasoning_trace", [])
    print(f"Trace entries logged ({len(trace)}):")
    for i, t in enumerate(trace, 1):
        print(f"  {i}. [{t['node']}]: {t['output_summary']}")
    assert len(trace) >= 3


def main():
    print("==================================================")
    print(" Running Phase 8: Pattern Extraction Tests        ")
    print("==================================================")
    try:
        test_prompt_file()
        test_pattern_extraction_and_stuck_topics()
        test_trace_chain()
        print("\n==================================================")
        print(" [ALL PHASE 8 TESTS PASSED] Pattern Engine Ready! ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
