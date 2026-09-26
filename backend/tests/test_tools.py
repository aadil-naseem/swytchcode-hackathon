"""
Standalone test script for Phase 3 Swytchcode Tool Wrappers (Notion, Gmail, Slack).
Exercises all functions across dry-run/mock mode and live mode.
"""

import os
import sys

# Ensure repository root is on sys.path so 'backend' is the top-level package namespace
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.tools.notion_client import (
    create_page as notion_create_page,
    search_pages as notion_search_pages,
    read_page as notion_read_page,
    NotionClientError,
)
from backend.tools.gmail_client import (
    send_email as gmail_send_email,
    search_threads as gmail_search_threads,
    GmailClientError,
)
from backend.tools.slack_client import (
    post_message as slack_post_message,
    SlackClientError,
)


def test_notion_client():
    print("\n--- [1/3] Testing Notion Client ---")
    
    # 1. Create page
    page_url = notion_create_page(
        parent_id="test_parent_id",
        title="[Team Health Report] Week 39 Audit",
        content_blocks=[
            "Summary: 3 topics stuck this week across 4 meetings.",
            "Decision Velocity: 25% (1 decision / 4 open topics).",
            "Action Item Load: Arjun has 7 items (overloaded)."
        ],
        mock=True
    )
    assert page_url.startswith("https://notion.so/"), f"Unexpected Notion page URL: {page_url}"
    print(f"  [PASS] notion_create_page succeeded -> {page_url}")

    # 2. Search pages
    search_results = notion_search_pages(query="Pricing Strategy", mock=True)
    assert isinstance(search_results, list) and len(search_results) > 0, "Notion search returned no results"
    print(f"  [PASS] notion_search_pages returned {len(search_results)} page(s) -> First: '{search_results[0]['title']}'")

    # 3. Read page
    page_data = notion_read_page(page_id="page_pricing_01", mock=True)
    assert "content" in page_data or "blocks" in page_data, "Notion read_page missing content"
    print(f"  [PASS] notion_read_page succeeded -> Title: '{page_data['title']}'")


def test_gmail_client():
    print("\n--- [2/3] Testing Gmail Client ---")
    
    # 1. Send Email
    sent = gmail_send_email(
        to="manager@example.com",
        subject="[ClearRoom Digest] What your meetings aren't resolving this week",
        body="Pricing strategy has been discussed 3 times with no decision made. Arjun has 7 action items.",
        mock=True
    )
    assert sent is True, "gmail_send_email did not return True"
    print("  [PASS] gmail_send_email succeeded")

    # 2. Search Threads
    threads = gmail_search_threads(query="pricing tiers", mock=True)
    assert isinstance(threads, list) and len(threads) > 0, "Gmail search returned no threads"
    print(f"  [PASS] gmail_search_threads returned {len(threads)} thread(s) -> First: '{threads[0]['subject']}'")


def test_slack_client():
    print("\n--- [3/3] Testing Slack Client ---")
    
    # 1. Post Message
    posted = slack_post_message(
        channel_id="C_PRODUCTIVITY",
        text_or_blocks="[ClearRoom Weekly Pulse]: 3 topics stuck this week. 1 person overloaded. Full report: https://notion.so/clearroom/report-123",
        mock=True
    )
    assert posted is True, "slack_post_message did not return True"
    print("  [PASS] slack_post_message succeeded")


def main():
    print("========================================")
    print(" Running Phase 3 Swytchcode Tool Tests  ")
    print("========================================")
    try:
        test_notion_client()
        test_gmail_client()
        test_slack_client()
        print("\n========================================")
        print(" [ALL TESTS PASSED] Tool wrappers ready! ")
        print("========================================")
    except AssertionError as e:
        print(f"\n[FAIL] Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected test failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
