"""
ClearRoom — Standalone Interactive CLI Demo Runner.
Serves as the functional safety net to run live demos directly in the terminal.

Usage:
  python backend/demo_cli.py --mode audit
  python backend/demo_cli.py --mode brief --topic "Pricing Strategy"
  python backend/demo_cli.py --prompt "I have a meeting tomorrow about Pricing Strategy — brief me"
"""

import os
import sys
import time
import argparse
import glob

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from backend.agent.graph import clearroom_agent
from backend.observability import format_trace_for_display


def load_sample_transcripts():
    fixtures_dir = os.path.join(REPO_ROOT, "backend", "tests", "fixtures")
    fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.txt")))
    transcripts = []
    for fpath in fixture_files:
        with open(fpath, "r", encoding="utf-8") as f:
            transcripts.append(f.read())
    return transcripts


def print_banner():
    print("\n" + "=" * 65)
    print(" [ClearRoom] AI Meeting Auditor & Lifecycle Agent")
    print(" Track: AI Meeting & Productivity Agent (Swytchcode Hackathon)")
    print(" Integrations: Notion | Gmail | Slack")
    print("=" * 65 + "\n")


def run_demo(mode: str = "audit", prompt: str = "", topic: str = "", dry_run: bool = True):
    print_banner()

    if dry_run:
        os.environ["DRY_RUN"] = "true"

    transcripts = load_sample_transcripts() if mode == "audit" or not prompt else []

    initial_state = {
        "mode": mode if not prompt else "",
        "prompt": prompt,
        "raw_meeting_notes": transcripts,
        "brief_topic": topic,
        "reasoning_trace": [],
        "errors": [],
    }

    print(f"[*] Dispatching ClearRoom Agent Execution...")
    if prompt:
        print(f"    Prompt: '{prompt}'")
    else:
        print(f"    Mode: {mode.upper()} ({len(transcripts)} meeting transcripts loaded)")

    print("-" * 65)
    start_time = time.perf_counter()
    final_state = clearroom_agent.invoke(initial_state)
    elapsed = time.perf_counter() - start_time
    print("-" * 65)

    trace = final_state.get("reasoning_trace", [])
    print(f"\n[AGENT REASONING & TOOL TRACE] ({len(trace)} Steps):")
    for step in trace:
        tool_str = ""
        if step.get("tool_calls"):
            tools = [f"{tc['tool']}:{tc['action']}" for tc in step["tool_calls"]]
            tool_str = f"  Tools: [{', '.join(tools)}]"
        print(f"  [{step['step']}] Node: {step['node']:<28} -> {step['decision']}{tool_str}")

    resolved_mode = final_state.get("mode", mode)
    print("\n" + "=" * 65)
    print(f" [PAYOFF MOMENT & LIVE ARTIFACTS] ({resolved_mode.upper()} MODE)")
    print("=" * 65)

    if resolved_mode == "audit":
        stuck = final_state.get("stuck_topics", [])
        if stuck:
            print(f"\n[!] STUCK TOPIC DETECTED:")
            print(f"    * Topic: {stuck[0].get('topic')}")
            print(f"    * Root Blocker: {stuck[0].get('blocking_reason')}")
            print(f"    * Suggested Owner: @{stuck[0].get('suggested_owner')}")
            print(f"    * Recommended Next Step: {stuck[0].get('suggested_next_step')}")

        overload = final_state.get("commitment_load", {}).get("overloaded_people", [])
        if overload:
            print(f"\n[!] WORKLOAD OVERLOAD ALERT:")
            print(f"    * {overload[0].get('name')} is carrying {overload[0].get('action_item_count')} action items ({overload[0].get('percentage_of_all_tasks')}% of team total).")

        print(f"\n[+] GENERATED ARTIFACTS & INTEGRATIONS:")
        print(f"    * Notion Team Health Report : {final_state.get('notion_report_url')}")
        if final_state.get("notion_decision_page_urls"):
            print(f"    * Notion Decision Page      : {final_state.get('notion_decision_page_urls')[0]}")
        print(f"    * Manager Gmail Digest Sent : {final_state.get('gmail_digest_sent')}")
        print(f"    * Slack Weekly Pulse Sent   : {final_state.get('slack_pulse_sent')}")

    else:
        brief = final_state.get("brief_output", {})
        print(f"\n[PRE-MEETING BRIEFING] Topic: '{final_state.get('brief_topic')}':")
        print(f"    * Past Decisions : {brief.get('past_decisions')}")
        print(f"    * Open Blockers  : {brief.get('open_loops_and_blockers')}")
        owners = [o.get("name") for o in brief.get("key_stakeholders_and_owners", [])]
        print(f"    * Key Drivers    : {', '.join(owners)}")
        print(f"    * Suggested Agenda:")
        for idx, item in enumerate(brief.get("suggested_agenda", []), 1):
            print(f"      {idx}. {item}")

    print(f"\n[i] Execution completed in {elapsed:.2f} seconds.")
    print("=" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="ClearRoom CLI Demo")
    parser.add_argument("--mode", choices=["audit", "brief"], default="audit", help="Execution mode")
    parser.add_argument("--prompt", type=str, default="", help="Natural language prompt")
    parser.add_argument("--topic", type=str, default="Pricing Strategy", help="Topic for brief mode")
    parser.add_argument("--live", action="store_true", help="Run with live API calls instead of dry-run")
    args = parser.parse_args()

    run_demo(
        mode=args.mode,
        prompt=args.prompt,
        topic=args.topic,
        dry_run=not args.live,
    )


if __name__ == "__main__":
    main()
