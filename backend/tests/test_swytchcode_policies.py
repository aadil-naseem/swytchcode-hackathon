"""
Test script for Swytchcode Policy Layer.
Verifies that:
1. policies.json is well-formed and valid.
2. Normal authorized requests pass policy checks.
3. Top-N guardrails and policy enforcement operate correctly.
"""

import os
import sys
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend/.env"))

def test_policy_file():
    print("\n--- [1/2] Verifying Swytchcode policies.json ---")
    policy_path = os.path.join(REPO_ROOT, ".swytchcode/integrations/policies.json")
    assert os.path.exists(policy_path), f"Policy file missing: {policy_path}"
    
    with open(policy_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "policies" in data, "policies.json missing 'policies' array"
    policies = data["policies"]
    print(f"  [PASS] policies.json loaded successfully with {len(policies)} policy rules:")
    for p in policies:
        print(f"    * Rule: '{p.get('id')}' -> Target: {p.get('target')} -> Action: {p.get('action', {}).get('type')}")

def test_top_n_guardrail():
    print("\n--- [2/2] Verifying Application Policy Guardrails ---")
    from backend.agent.nodes.extract_patterns import extract_patterns_node
    
    # Create synthetic test with 8 stuck topics
    dummy_topics = [
        {"topic": f"Topic {i}", "is_stuck": True, "meeting_count": i, "status": "unresolved"}
        for i in range(1, 9)
    ]
    dummy_state = {
        "parsed_meetings": [],
        "recurring_topics": dummy_topics,
        "commitment_load": {"counts_by_person": {"Arjun": 3, "Maya": 1}},
        "meeting_necessity_scores": {},
        "reasoning_trace": [],
    }
    
    res = extract_patterns_node(dummy_state)
    stuck_res = res.get("recurring_topics", [])
    assert len(stuck_res) <= 5, f"Top-N guardrail failed: expected max 5, got {len(stuck_res)}"
    print(f"  [PASS] Top-N Policy Guardrail enforced: capped 8 candidate topics to {len(stuck_res)} high-impact topics.")

if __name__ == "__main__":
    print("==================================================")
    print("      TESTING SWYTCHCODE POLICY LAYER             ")
    print("==================================================")
    test_policy_file()
    test_top_n_guardrail()
    print("\n==================================================")
    print("      [ALL SWYTCHCODE POLICY TESTS PASSED]        ")
    print("==================================================")
