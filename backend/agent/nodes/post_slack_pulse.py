"""
Phase 12 & 14 - Audit Mode: Slack Weekly Pulse Node.
"""

import os
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools import slack_post_message, SlackClientError
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("meetloop.agent.slack_pulse")


def _compose_slack_pulse_blocks(state: ClearRoomState) -> List[Dict[str, Any]]:
    stuck_topics = state.get("stuck_topics") or []
    commitment_load = state.get("commitment_load") or {}
    report_url = state.get("notion_report_url", "https://notion.so/meetloop/health-report")
    decision_urls = state.get("notion_decision_page_urls") or []

    overloaded_people = commitment_load.get("overloaded_people", [])
    stuck_count = len(stuck_topics)
    overload_count = len(overloaded_people)

    overload_str = f"{overload_count} teammate carrying high load" if overload_count > 0 else "workload balanced"
    header_text = f"*MeetLoop Weekly Meeting Audit*\n>{stuck_count} stuck topic{'s' if stuck_count != 1 else ''} this week • {overload_str}."

    blocks: List[Dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": header_text,
            },
        },
        {"type": "divider"},
    ]

    if stuck_topics:
        stuck_lines = ["*Stuck Topics Requiring Decision:*"]
        for idx, item in enumerate(stuck_topics[:3], 1):
            topic_name = item.get("topic", "Untitled")
            owner = item.get("suggested_owner", "unassigned")
            blocker = item.get("blocking_reason", "alignment needed")
            dec_link = f" (<{decision_urls[idx-1]}|Decision Page>)" if idx <= len(decision_urls) else ""
            stuck_lines.append(f"• *{topic_name}*: {blocker} -> Driver: @{owner}{dec_link}")

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(stuck_lines),
            },
        })

    if overloaded_people:
        overload_lines = ["*Workload Alert:*"]
        for p in overloaded_people:
            overload_lines.append(
                f"• *{p.get('name')}* has {p.get('action_item_count')} action items ({p.get('percentage_of_all_tasks')}% of team total)."
            )
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\n".join(overload_lines),
            },
        })

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"📋 *Full Notion Team Health Report:* <{report_url}|View Report in Notion>",
        },
    })

    return blocks


def post_slack_pulse_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: post_slack_pulse] Composing and posting weekly pulse to Slack...")

    channel_id = os.getenv("SLACK_CHANNEL_ID", "C_MEETLOOP_ALERTS")
    pulse_blocks = _compose_slack_pulse_blocks(state)

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )

    errors = list(state.get("errors") or [])
    sent_successfully = False

    try:
        sent_successfully = slack_post_message(
            channel_id=channel_id,
            text_or_blocks=pulse_blocks,
            mock=is_dry_run,
        )
    except Exception as e:
        logger.warning(f"Failed to post Slack pulse (soft-fail): {e}")
        errors.append({
            "node": "post_slack_pulse",
            "error_type": type(e).__name__,
            "message": str(e),
        })
        sent_successfully = False

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="post_slack_pulse",
        what_it_decided="Published pulse update to team Slack channel" if sent_successfully else "Slack pulse soft-failed (logged in errors)",
        input_summary=f"Composed pulse message for channel {channel_id}",
        output_summary=f"Slack pulse sent: {sent_successfully}",
        tool_calls=[{"tool": "Slack", "action": "post_message", "channel": channel_id}],
        status="success" if sent_successfully else "warning",
    )

    return {
        "slack_pulse_sent": sent_successfully,
        "errors": errors,
        "reasoning_trace": new_trace,
    }
