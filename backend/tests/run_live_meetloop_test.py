"""
Live execution of MeetLoop AI agent on the synthetic PulseBoard meeting notes.
Executes real Swytchcode tool calls:
- Creates Real Notion Health Report & Decision Pages
- Sends Real Gmail Executive Digest
- Posts Real Slack Channel Pulse
"""

import os
import sys

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(REPO_ROOT, "backend/.env"))

# Explicitly ensure DRY_RUN is false for this live run
os.environ["DRY_RUN"] = "false"
os.environ["MOCK_TOOLS"] = "false"

from backend.agent.graph import clearroom_agent

RAW_NOTES = """Title: PulseBoard Weekly Product Sync
Date: 2026-09-28
Duration: 48 minutes
Participants: Maya (Product Manager), Arjun (Backend Engineer), Sofia (Frontend Engineer), Daniel (ML Engineer), Riya (Designer)

PulseBoard weekly sync — Monday

Maya started by asking why the onboarding redesign is still not in staging.

Sofia said most of the frontend work is done but the new onboarding screens depend on the backend profile API.

Arjun said profile API is technically ready but he hasn't merged it because Daniel changed the user-event schema last week.

Daniel said the schema change was needed because analytics wasn't capturing onboarding_step correctly.

Maya asked whether we actually need the schema change now or whether we can ship onboarding first and fix analytics later.

Daniel: probably yes but then we'd have to migrate events twice.

Sofia said from frontend side they can work with the old API for now but it would mean doing some extra mapping.

Maya asked if that means onboarding can go to staging this week.

Arjun said "probably Thursday" but only if Daniel confirms the schema today.

Daniel said he needs to check with Riya because some of the event names came from the new UX flow.

Riya said she thought those event names were already finalized last Friday.

Maya: I don't think we ever actually finalized them.

Everyone talked for a few minutes about event naming.

Decision seemed to be that Daniel and Riya would review the event names today and post the final list.

Maya asked who owns the migration if the schema changes.

Arjun said he can do it but he doesn't want to own it unless the schema is final.

No explicit owner was assigned for the migration.

Then they discussed the onboarding completion rate.

Current completion rate around 61%.

Maya wants to push it to 75% with the redesign.

Daniel said he also noticed duplicate events being fired on mobile web.

Arjun: is that blocking staging?

Daniel: not blocking staging but we shouldn't run A/B test with duplicate events.

Action items mentioned:
- Daniel to check analytics schema
- Riya to confirm UX event names
- Sofia to finish frontend mapping if needed
- Arjun to wait for schema before merging profile API

Meeting ended without a clear launch date for staging.
"""

def run_live():
    print("=======================================================")
    print("     EXECUTING LIVE MEETLOOP RUN VIA SWYTCHCODE        ")
    print("=======================================================")
    print(f"[*] Notion Parent Page ID : {os.getenv('NOTION_HEALTH_REPORT_PARENT_PAGE_ID')}")
    print(f"[*] Gmail Recipient / Test: {os.getenv('GMAIL_TEST_ACCOUNT')}")
    print(f"[*] Slack Channel ID      : {os.getenv('SLACK_CHANNEL_ID')}")
    print("=======================================================\n")

    initial_state = {
        "raw_input": RAW_NOTES,
        "mode": "audit",
        "errors": [],
    }

    final_state = clearroom_agent.invoke(initial_state)

    print("\n=======================================================")
    print("          LIVE MEETLOOP AUDIT EXECUTION COMPLETE       ")
    print("=======================================================")

    print("\n[REAL EXTERNAL SIDE EFFECTS GENERATED]:")
    print(f"  * Notion Health Report URL : {final_state.get('notion_report_url')}")
    print(f"  * Notion Decision Page URLs: {final_state.get('notion_decision_page_urls')}")
    print(f"  * Gmail Digest Sent        : {final_state.get('gmail_digest_sent')}")
    print(f"  * Slack Pulse Sent         : {final_state.get('slack_pulse_sent')}")
    print(f"  * Errors                   : {final_state.get('errors')}")

    print("\n[REASONING TRACE LOGGED]:")
    for step in final_state.get("reasoning_trace", []):
        tools = [t.get("tool") for t in step.get("tool_calls", [])] if step.get("tool_calls") else []
        tools_str = f" -> Tools: {tools}" if tools else ""
        print(f"  [{step.get('node_name', ''):<26}] -> {step.get('what_it_decided')}{tools_str}")

    return final_state

if __name__ == "__main__":
    run_live()
