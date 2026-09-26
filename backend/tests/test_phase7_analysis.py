"""
Test script for Phase 7: Audit Mode Cross-Meeting Analysis (Core Reasoning).
Validates schema compliance, stuck topic detection, and commitment load detection across fixtures.
"""

import os
import sys
import glob

# Set dry-run mode for offline test execution to preserve OpenRouter quota
os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.nodes.analyze_meetings import analyze_meetings_node, PROMPT_PATH


def load_all_fixtures():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def test_prompt_file_exists():
    print("\n--- [1/3] Checking System Prompt File ---")
    assert os.path.exists(PROMPT_PATH), f"System prompt not found at {PROMPT_PATH}"
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "recurring_topics" in content
    assert "decision_velocity" in content
    assert "commitment_load" in content
    assert "meeting_necessity_scores" in content
    print(f"  [PASS] System prompt exists and contains full schema definitions ({len(content)} chars).")


def test_cross_meeting_reasoning_node():
    print("\n--- [2/3] Testing Cross-Meeting Reasoning on 4 Fixtures ---")
    transcripts = load_all_fixtures()
    assert len(transcripts) == 4, f"Expected 4 fixtures, found {len(transcripts)}"

    initial_state = {
        "mode": "audit",
        "raw_meeting_notes": transcripts,
        "reasoning_trace": [],
    }

    result = analyze_meetings_node(initial_state)

    # 1. Check recurring & stuck topics
    recurring = result.get("recurring_topics", [])
    assert len(recurring) > 0, "No recurring topics found!"
    stuck = [t for t in recurring if t.get("is_stuck")]
    assert len(stuck) > 0, "Failed to detect the planted stuck topic!"
    stuck_topic = stuck[0]
    print(f"  [PASS] Detected Stuck Topic: '{stuck_topic['topic']}' (Discussed in {stuck_topic.get('meeting_count', 0)} meetings)")
    assert "Pricing" in stuck_topic["topic"]
    assert stuck_topic.get("meeting_count") == 3

    # 2. Check commitment load & overload detection
    commitment = result.get("commitment_load", {})
    counts = commitment.get("counts_by_person", {})
    overloaded = commitment.get("overloaded_people", [])
    assert len(overloaded) > 0, "Failed to flag overloaded team member!"
    top_overloaded = overloaded[0]
    print(f"  [PASS] Detected Overloaded Person: '{top_overloaded['name']}' with {top_overloaded['action_item_count']} action items ({top_overloaded['percentage_of_all_tasks']:.1f}% of total)")
    assert top_overloaded["name"] == "Arjun"
    assert top_overloaded["action_item_count"] == 7

    # 3. Check decision velocity & necessity scores
    necessity = result.get("meeting_necessity_scores", {})
    assert len(necessity) > 0, "Missing meeting necessity scores!"
    standup_score = next((v for k, v in necessity.items() if "Standup" in k or "Tuesday" in k), None)
    retro_score = next((v for k, v in necessity.items() if "Retrospective" in k or "Friday" in k), None)
    assert standup_score is not None, "Tuesday standup score missing"
    assert retro_score is not None, "Friday retro score missing"

    print(f"  [PASS] Tuesday Standup Necessity: {standup_score['necessity_score']}/10 -> Recommendation: '{standup_score['recommendation']}'")
    print(f"  [PASS] Friday Retro Necessity: {retro_score['necessity_score']}/10 -> Recommendation: '{retro_score['recommendation']}'")
    assert "Async" in standup_score["recommendation"]
    assert retro_score["necessity_score"] >= 8


def test_trace_logging():
    print("\n--- [3/3] Testing Trace Entry ---")
    transcripts = load_all_fixtures()
    result = analyze_meetings_node({"raw_meeting_notes": transcripts, "reasoning_trace": []})
    trace = result.get("reasoning_trace", [])
    assert len(trace) > 0, "No trace recorded"
    print(f"  [PASS] Trace Summary: {trace[0]['output_summary']}")


def main():
    print("==================================================")
    print(" Running Phase 7: Cross-Meeting Reasoning Tests   ")
    print("==================================================")
    try:
        test_prompt_file_exists()
        test_cross_meeting_reasoning_node()
        test_trace_logging()
        print("\n==================================================")
        print(" [ALL PHASE 7 TESTS PASSED] Core Reasoning Ready! ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
