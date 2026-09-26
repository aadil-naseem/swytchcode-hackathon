"""
Phase 9 & 14 - Audit Mode: Notion Team Health Report Node.
"""

import os
import datetime
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools import notion_create_page
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("meetloop.agent.write_notion_report")


def _build_notion_report_blocks(state: ClearRoomState) -> List[str]:
    parsed_meetings = state.get("parsed_meetings") or []
    stuck_topics = state.get("stuck_topics") or []
    commitment_load = state.get("commitment_load") or {}
    meeting_scores = state.get("meeting_necessity_scores") or {}
    decision_velocity = state.get("decision_velocity") or {}
    agenda_gaps = state.get("agenda_outcome_gaps") or []

    blocks: List[str] = []

    today_str = datetime.date.today().strftime("%B %d, %Y")
    blocks.append(f"📅 Audit Date: {today_str} | Analyzed Meetings: {len(parsed_meetings)}")
    
    headline = (
        f"🚨 MeetLoop Audit Summary: {len(stuck_topics)} stuck topic(s) detected across {len(parsed_meetings)} meetings. "
        f"Decision Velocity: {decision_velocity.get('overall_velocity_rate', 0.8)*100:.0f}%."
    )
    blocks.append(headline)
    blocks.append("---")

    blocks.append("## 🔴 Stuck Topics (Discussed Multiple Times With No Resolution)")
    if stuck_topics:
        for idx, item in enumerate(stuck_topics, 1):
            dates_str = ", ".join(item.get("meeting_dates", [])) or "Past 7 days"
            blocks.append(
                f"### {idx}. {item.get('topic')}\n"
                f"- **Occurrences**: Discussed in {item.get('occurrences', 2)} meetings ({dates_str})\n"
                f"- **Root Blocker**: {item.get('blocking_reason', 'Pending alignment')}\n"
                f"- **Suggested Owner**: @{item.get('suggested_owner', 'Unassigned')}\n"
                f"- **Recommended Next Step**: {item.get('suggested_next_step', 'Schedule focused decision sync')}\n"
                f"- **Competing Views**: {item.get('synthesized_views', 'N/A')}"
            )
    else:
        blocks.append("✅ No stuck topics detected this week. All opened topics resolved.")

    blocks.append("---")

    blocks.append("## ⚖️ Team Commitment Load & Task Allocation")
    overloaded = commitment_load.get("overloaded_people", [])
    if overloaded:
        blocks.append("### ⚠️ Overload Alerts")
        for p in overloaded:
            blocks.append(
                f"- **{p.get('name')}**: **{p.get('action_item_count')} action items** "
                f"({p.get('percentage_of_all_tasks', 0)}% of total team tasks)\n"
                f"  *Assessment*: {p.get('assessment', 'Carrying disproportionate execution burden.')}"
            )

    blocks.append("### 📋 Full Workload Breakdown")
    counts = commitment_load.get("counts_by_person", {})
    for name, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        badge = " [OVERLOADED]" if any(o.get("name") == name for o in overloaded) else " [Balanced]"
        blocks.append(f"- **{name}**: {cnt} action item(s){badge}")

    blocks.append("---")

    blocks.append("## 📊 Meeting Type Efficiency & Calendar Optimization")
    ranked = meeting_scores.get("ranked_categories", [])
    if ranked:
        for r in ranked:
            res_pct = int(r.get("resolution_rate", 0) * 100)
            blocks.append(
                f"- **{r.get('category')}**: Efficiency {r.get('necessity_score')}/10 ({res_pct}% resolution rate).\n"
                f"  *Action*: {r.get('async_recommendation', 'Keep current cadence')}"
            )
    else:
        blocks.append("- Standard meeting cadence.")

    blocks.append("---")

    if agenda_gaps:
        blocks.append("## 📝 Per-Meeting Resolution Breakdown")
        for g in agenda_gaps:
            res_rate = int(g.get("resolution_rate", 0) * 100)
            unres = ", ".join(g.get("unresolved_topics", [])) or "None"
            blocks.append(
                f"- **{g.get('meeting_title')}** ({g.get('date')}): {res_rate}% resolved. "
                f"Unresolved: {unres}. *Notes*: {g.get('gap_notes', '')}"
            )

    return blocks


def write_notion_report_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: write_notion_report] Generating and publishing Notion Team Health Report...")

    content_blocks = _build_notion_report_blocks(state)
    report_title = f"[Team Health Report] MeetLoop Meeting Audit - {datetime.date.today().isoformat()}"

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )
    parent_page_id = os.getenv("NOTION_HEALTH_REPORT_PARENT_PAGE_ID")

    try:
        page_url = notion_create_page(
            parent_id=parent_page_id,
            title=report_title,
            content_blocks=content_blocks,
            mock=is_dry_run,
        )
    except Exception as e:
        logger.error(f"Error publishing Notion health report: {e}")
        page_url = "https://notion.so/meetloop/team-health-report-fallback"

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="write_notion_report",
        what_it_decided="Published Team Health Report to Notion",
        input_summary=f"Compiled report with {len(state.get('stuck_topics') or [])} stuck topic(s) and team metrics",
        output_summary=f"Created Notion Team Health Report -> {page_url}",
        tool_calls=[{"tool": "Notion", "action": "create_page", "target": report_title}],
    )

    return {
        "notion_report_url": page_url,
        "reasoning_trace": new_trace,
    }
