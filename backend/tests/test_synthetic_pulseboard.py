"""
Test script for the synthetic PulseBoard meeting notes.
Executes the full ClearRoom agent pipeline and verifies all 4 evaluation layers.
"""

import os
import sys

os.environ["DRY_RUN"] = "true"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

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

Maya wants it above 70%.

Daniel said the analytics numbers might be wrong because some events are duplicated.

Riya thinks the new onboarding is visually much simpler and should improve completion.

Sofia said we shouldn't judge the redesign until we have clean analytics.

Maya asked if they can run an A/B test.

Daniel said technically yes but setting it up would take about 2 days.

Maya said let's do it after the redesign reaches staging.

Arjun asked whether the team should prioritize the mobile onboarding bug instead.

There was discussion about mobile users being around 35% of traffic.

Sofia said the mobile bug is annoying but doesn't block the main onboarding flow.

Maya said "okay, let's not expand scope."

Then discussion moved back to release timing.

Maya suggested Thursday for staging and Friday for A/B test preparation.

Daniel said Friday might be optimistic because analytics instrumentation still isn't stable.

No one challenged Thursday directly.

Maya ended with:
- Daniel + Riya finalize event names today
- Arjun prepare profile API changes once schema is confirmed
- Sofia finish frontend integration
- A/B test plan to be discussed Friday

But there wasn't a clear owner for coordinating the overall release.

Meeting ended after another discussion about whether the analytics issue should be fixed before staging.

Final outcome wasn't completely clear.
"""


def run_pulseboard_audit():
    initial_state = {
        "mode": "audit",
        "raw_meeting_notes": [RAW_NOTES],
        "reasoning_trace": [],
        "errors": [],
    }

    print("\n[*] Invoking ClearRoom Agent on PulseBoard Raw Notes...")
    final_state = clearroom_agent.invoke(initial_state)

    print("\n=======================================================")
    print("           PULSEBOARD MEETING AUDIT RESULTS            ")
    print("=======================================================")

    trace = final_state.get("reasoning_trace", [])
    print(f"\n[LAYER 1 & 2: REASONING & PIPELINE TRACE] ({len(trace)} Steps):")
    for step in trace:
        tools = ""
        if step.get("tool_calls"):
            tools = f" -> Tools: {[tc['tool'] for tc in step['tool_calls']]}"
        print(f"  Step {step['step']}: [{step['node']:<28}] -> {step['decision']}{tools}")

    print("\n[DECISION INTELLIGENCE FINDINGS]:")
    stuck = final_state.get("stuck_topics", [])
    if stuck:
        print(f"\n[!] STUCK TOPICS & UNRESOLVED ISSUES ({len(stuck)}):")
        for idx, item in enumerate(stuck, 1):
            print(f"  {idx}. Topic: {item.get('topic')}")
            print(f"     * Root Blocker: {item.get('blocking_reason')}")
            print(f"     * Suggested Owner: @{item.get('suggested_owner')}")
            print(f"     * Recommended Next Step: {item.get('suggested_next_step')}")
            print(f"     * Competing Views: {item.get('synthesized_views')}")

    comm = final_state.get("commitment_load", {})
    counts = comm.get("counts_by_person", {})
    print(f"\n[!] COMMITMENT LOAD BREAKDOWN:")
    for person, count in counts.items():
        print(f"  * {person}: {count} action item(s)")

    overloaded = comm.get("overloaded_people", [])
    if overloaded:
        print(f"\n[!] OVERLOAD ALERTS:")
        for p in overloaded:
            print(f"  * {p.get('name')}: {p.get('action_item_count')} tasks ({p.get('percentage_of_all_tasks')}%) - {p.get('assessment')}")

    necessity = final_state.get("meeting_necessity_scores", {})
    print(f"\n[!] MEETING NECESSITY & CALENDAR OPTIMIZATION:")
    for m_name, sc in necessity.items():
        if isinstance(sc, dict) and "necessity_score" in sc:
            print(f"  * {m_name}: Score {sc.get('necessity_score')}/10 | Rec: {sc.get('recommendation')} ({sc.get('reasoning')})")

    print("\n[LAYER 3: EXTERNAL SIDE EFFECTS GENERATED]:")
    print(f"  * Notion Health Report URL : {final_state.get('notion_report_url')}")
    print(f"  * Notion Decision Page URLs: {final_state.get('notion_decision_page_urls')}")
    print(f"  * Gmail Digest Sent        : {final_state.get('gmail_digest_sent')}")
    print(f"  * Slack Pulse Sent         : {final_state.get('slack_pulse_sent')}")


if __name__ == "__main__":
    run_pulseboard_audit()
