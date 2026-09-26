"""
Test script for Phase 13: Brief Mode (Pre-Meeting Intelligence).
Verifies natural language intent classification, Notion + Gmail context retrieval,
and grounded briefing synthesis through the LangGraph agent.
"""

import os
import sys

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.graph import clearroom_agent
from backend.agent.nodes.classify_input import classify_input_node
from backend.agent.nodes.search_notion import search_notion_node
from backend.agent.nodes.search_gmail import search_gmail_node
from backend.agent.nodes.generate_brief import generate_brief_node, PROMPT_PATH


def test_prompt_file():
    print("\n--- [1/4] Checking Pre-Meeting Brief Prompt ---")
    assert os.path.exists(PROMPT_PATH), f"Prompt not found at {PROMPT_PATH}"
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "past_decisions" in content
    assert "open_loops_and_blockers" in content
    assert "key_stakeholders_and_owners" in content
    assert "suggested_agenda" in content
    print(f"  [PASS] Brief prompt file exists with full schema ({len(content)} chars).")


def test_intent_classification():
    print("\n--- [2/4] Testing Natural Language Intent Routing & Topic Extraction ---")

    # Test A: Natural language brief prompt
    state_a = {"prompt": "I have a meeting tomorrow about Pricing Strategy — brief me", "reasoning_trace": []}
    res_a = classify_input_node(state_a)
    assert res_a.get("mode") == "brief", f"Expected brief mode, got {res_a.get('mode')}"
    assert "Pricing" in res_a.get("brief_topic", ""), f"Failed to extract topic: {res_a.get('brief_topic')}"
    print(f"  [PASS] Prompt: '{state_a['prompt']}' -> Mode: '{res_a['mode']}', Topic: '{res_a['brief_topic']}'")

    # Test B: Audit prompt
    state_b = {"prompt": "Audit past meetings from this week", "reasoning_trace": []}
    res_b = classify_input_node(state_b)
    assert res_b.get("mode") == "audit"
    print(f"  [PASS] Prompt: '{state_b['prompt']}' -> Mode: '{res_b['mode']}'")


def test_context_retrieval_and_synthesis():
    print("\n--- [3/4] Testing Notion + Gmail Context Retrieval and Brief Synthesis ---")
    state = {
        "mode": "brief",
        "brief_topic": "Pricing Strategy",
        "reasoning_trace": [],
    }

    # Step 1: Search Notion
    state.update(search_notion_node(state))
    notion_results = state.get("notion_search_results", [])
    assert len(notion_results) > 0, "No Notion pages returned"
    print(f"  [PASS] Retrieved {len(notion_results)} Notion doc(s) -> First: '{notion_results[0]['title']}'")

    # Step 2: Search Gmail
    state.update(search_gmail_node(state))
    gmail_results = state.get("gmail_search_results", [])
    assert len(gmail_results) > 0, "No Gmail threads returned"
    print(f"  [PASS] Retrieved {len(gmail_results)} Gmail thread(s) -> First: '{gmail_results[0]['subject']}'")

    # Step 3: Synthesize Brief
    state.update(generate_brief_node(state))
    brief = state.get("brief_output", {})

    print(f"\n--- Synthesized Pre-Meeting Brief ---")
    print(f"  • Topic: {brief.get('topic')}")
    print(f"  • Past Decisions: {brief.get('past_decisions')}")
    print(f"  • Open Blockers: {brief.get('open_loops_and_blockers')}")
    owners = [o.get("name") for o in brief.get("key_stakeholders_and_owners", [])]
    print(f"  • Key Stakeholders: {', '.join(owners)}")
    print(f"  • Suggested Agenda Items: {len(brief.get('suggested_agenda', []))}")

    assert brief.get("topic") == "Pricing Strategy"
    assert "Agreed" in brief.get("past_decisions", "") or "tier" in brief.get("past_decisions", "").lower()
    assert "survey" in brief.get("open_loops_and_blockers", "").lower() or "token" in brief.get("open_loops_and_blockers", "").lower()
    assert "Arjun" in owners

    print("\n[PASS] Pre-meeting brief synthesized and grounded in real context!")


def test_full_brief_mode_graph_execution():
    print("\n--- [4/4] Testing Full Brief Mode Graph Execution via LangGraph ---")
    initial_input = {
        "prompt": "I have a meeting tomorrow about Pricing Strategy — brief me",
        "reasoning_trace": [],
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_input)

    assert final_state.get("mode") == "brief"
    assert final_state.get("brief_output") is not None
    assert len(final_state.get("notion_search_results", [])) > 0
    assert len(final_state.get("gmail_search_results", [])) > 0

    trace = final_state.get("reasoning_trace", [])
    print(f"Trace Steps ({len(trace)}):")
    for i, t in enumerate(trace, 1):
        print(f"  {i}. [{t['node']}] -> {t['decision']}")

    print("\n[PASS] LangGraph Brief Mode executed all nodes in order!")


def main():
    print("==================================================")
    print(" Running Phase 13: Brief Mode Tests               ")
    print("==================================================")
    try:
        test_prompt_file()
        test_intent_classification()
        test_context_retrieval_and_synthesis()
        test_full_brief_mode_graph_execution()
        print("\n==================================================")
        print(" [ALL PHASE 13 TESTS PASSED] Brief Mode Complete! ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
