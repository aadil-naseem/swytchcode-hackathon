"""
Phase 11 & 14 - Audit Mode: Gmail Digest Node.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools import gmail_send_email, GmailClientError
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("meetloop.agent.gmail_digest")


def _compose_gmail_digest_body(state: ClearRoomState) -> str:
    stuck_topics = state.get("stuck_topics") or []
    commitment_load = state.get("commitment_load") or {}
    meeting_scores = state.get("meeting_necessity_scores") or {}
    report_url = state.get("notion_report_url", "https://notion.so/meetloop/health-report")
    decision_urls = state.get("notion_decision_page_urls") or []

    overloaded_people = commitment_load.get("overloaded_people", [])
    ranked_meetings = meeting_scores.get("ranked_categories", [])

    lines: List[str] = [
        "Hi Manager,",
        "",
        "Here is what your team's meetings did NOT resolve this week, analyzed across all syncs by MeetLoop AI:",
        "",
        "--------------------------------------------------",
        "[STUCK TOPICS] (Discussed 2+ times with 0 decisions):",
        "--------------------------------------------------"
    ]

    if stuck_topics:
        for idx, item in enumerate(stuck_topics[:3], 1):
            lines.append(f"{idx}. {item.get('topic')}")
            lines.append(f"   * Debated in: {item.get('occurrences', 2)} meetings")
            lines.append(f"   * Blocker: {item.get('blocking_reason', 'Pending alignment')}")
            lines.append(f"   * Suggested Driver: @{item.get('suggested_owner', 'Unassigned')}")
            lines.append(f"   * Action Step: {item.get('suggested_next_step', 'Schedule decision sync')}")
            if idx <= len(decision_urls):
                lines.append(f"   * Decision Page: {decision_urls[idx - 1]}")
            lines.append("")
    else:
        lines.append("* No recurring stuck topics detected this week.")
        lines.append("")

    lines.extend([
        "--------------------------------------------------",
        "[TEAM COMMITMENT & OVERLOAD ALERTS]:",
        "--------------------------------------------------"
    ])

    if overloaded_people:
        for p in overloaded_people:
            lines.append(
                f"! {p.get('name')} is OVERLOADED with {p.get('action_item_count')} action items "
                f"({p.get('percentage_of_all_tasks')}% of entire team load)."
            )
            lines.append(f"   Assessment: {p.get('assessment', 'Bottleneck risk.')}")
            lines.append("")
    else:
        lines.append("* Action item distribution across the team is balanced.")
        lines.append("")

    lines.extend([
        "--------------------------------------------------",
        "[CALENDAR EFFICIENCY INSIGHT]:",
        "--------------------------------------------------"
    ])

    if ranked_meetings:
        least_eff = ranked_meetings[0]
        lines.append(
            f"* Lowest Velocity: {least_eff.get('category')} resolved {least_eff.get('topics_resolved')}/{least_eff.get('topics_opened')} topics ({int(least_eff.get('resolution_rate', 0)*100)}%)."
        )
        lines.append(f"  -> Recommendation: {least_eff.get('async_recommendation', 'Convert to async')}")
        lines.append("")

    lines.extend([
        "--------------------------------------------------",
        f"FULL NOTION TEAM HEALTH REPORT: {report_url}",
        "--------------------------------------------------",
        "",
        "Best regards,",
        "MeetLoop Meeting Auditor"
    ])

    return "\n".join(lines)


def send_gmail_digest_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: send_gmail_digest] Composing and sending manager digest email...")

    recipient = os.getenv("GMAIL_TEST_ACCOUNT", "manager@company.internal")
    subject = "[MeetLoop Audit] Here's what your meetings aren't resolving this week"
    body = _compose_gmail_digest_body(state)

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )

    errors = list(state.get("errors") or [])
    sent_successfully = False

    try:
        sent_successfully = gmail_send_email(
            to=recipient,
            subject=subject,
            body=body,
            mock=is_dry_run,
        )
    except Exception as e:
        logger.warning(f"Failed to send Gmail digest (soft-fail): {e}")
        errors.append({
            "node": "send_gmail_digest",
            "error_type": type(e).__name__,
            "message": str(e),
        })
        sent_successfully = False

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="send_gmail_digest",
        what_it_decided="Sent manager executive digest via Gmail" if sent_successfully else "Gmail digest soft-failed (logged in errors)",
        input_summary=f"Prepared digest for {recipient} summarizing {len(state.get('stuck_topics') or [])} stuck topic(s)",
        output_summary=f"Gmail digest sent: {sent_successfully}",
        tool_calls=[{"tool": "Gmail", "action": "send_email", "recipient": recipient}],
        status="success" if sent_successfully else "warning",
    )

    return {
        "gmail_digest_sent": sent_successfully,
        "errors": errors,
        "reasoning_trace": new_trace,
    }
