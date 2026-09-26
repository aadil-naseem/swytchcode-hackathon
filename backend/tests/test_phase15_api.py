"""
Test script for Phase 15: FastAPI Backend & API Contract.
Validates /health, /fixtures, and POST /run (Audit & Brief mode) endpoints via TestClient.
"""

import os
import sys
from fastapi.testclient import TestClient

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.api.main import app

client = TestClient(app)


def test_health_endpoint():
    print("\n--- [1/4] Testing GET /health Endpoint ---")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed with {resp.status_code}"
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Notion" in data["integrations"]
    assert "Gmail" in data["integrations"]
    assert "Slack" in data["integrations"]
    print(f"  [PASS] Health check returned 200 OK: {data['service']}")


def test_fixtures_endpoint():
    print("\n--- [2/4] Testing GET /fixtures Endpoint ---")
    resp = client.get("/fixtures")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 4
    assert len(data["fixtures"]) >= 4
    print(f"  [PASS] Fixtures endpoint returned {data['count']} demo transcripts.")


def test_post_run_audit_mode():
    print("\n--- [3/4] Testing POST /run in AUDIT MODE ---")
    payload = {
        "mode": "audit",
        "dry_run": True,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200, f"POST /run failed: {resp.text}"
    data = resp.json()

    assert data["status"] == "success"
    assert data["mode"] == "audit"
    assert data["notion_report_url"] is not None
    assert len(data["stuck_topics"]) > 0
    assert len(data["reasoning_trace"]) == 8
    assert data["gmail_digest_sent"] is True
    assert data["slack_pulse_sent"] is True

    print(f"  [PASS] Audit mode returned 200 OK.")
    print(f"         Summary Insight: '{data['summary_insight']}'")
    print(f"         Reasoning Steps in API payload: {len(data['reasoning_trace'])}")
    print(f"         Notion Report URL: {data['notion_report_url']}")


def test_post_run_brief_mode():
    print("\n--- [4/4] Testing POST /run in BRIEF MODE ---")
    payload = {
        "prompt": "I have a meeting tomorrow about Pricing Strategy — brief me",
        "dry_run": True,
    }
    resp = client.post("/run", json=payload)
    assert resp.status_code == 200, f"POST /run brief failed: {resp.text}"
    data = resp.json()

    assert data["status"] == "success"
    assert data["mode"] == "brief"
    assert data["brief_output"] is not None
    assert len(data["reasoning_trace"]) == 4

    print(f"  [PASS] Brief mode returned 200 OK.")
    print(f"         Extracted Topic: '{data['brief_topic']}'")
    print(f"         Brief Summary: '{data['brief_output'].get('executive_summary')[:90]}...'")
    print(f"         Reasoning Steps in API payload: {len(data['reasoning_trace'])}")


def main():
    print("==================================================")
    print(" Running Phase 15: FastAPI API Contract Tests     ")
    print("==================================================")
    try:
        test_health_endpoint()
        test_fixtures_endpoint()
        test_post_run_audit_mode()
        test_post_run_brief_mode()
        print("\n==================================================")
        print(" [ALL PHASE 15 TESTS PASSED] FastAPI Layer Ready! ")
        print("==================================================")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
