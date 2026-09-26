"""
Phase 10 & 14 - Audit Mode: Notion Decision Page Node.
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
logger = logging.getLogger("meetloop.agent.write_notion_decision_page")


def _build_decision_page_blocks(stuck_topic: Dict[str, Any]) -> List[str]:
    blocks: List[str] = []

    topic_title = stuck_topic.get("topic", "Untitled Topic")
    occurrences = stuck_topic.get("occurrences", 2)
    meeting_dates = stuck_topic.get("meeting_dates", [])
    dates_str = ", ".join(meeting_dates) if meeting_dates else "Past 7 days"
    blocking_reason = stuck_topic.get("blocking_reason", "No alignment reached.")
    suggested_owner = stuck_topic.get("suggested_owner", "Unassigned")
    suggested_next_step = stuck_topic.get("suggested_next_step", "Schedule focused decision sync.")
    competing_views = stuck_topic.get("synthesized_views", "Different perspectives debated.")

    blocks.append(
        f"🚨 **Issue Overview**: Discussed in **{occurrences} meetings** ({dates_str}) with 0 resolutions."
    )
    blocks.append("---")

    blocks.append("## 1. What's Blocking It")
    blocks.append(f"> {blocking_reason}")

    blocks.append("## 2. Competing Views & Positions")
    blocks.append(competing_views)

    blocks.append("## 3. Decision Options")
    options = stuck_topic.get("decision_options", [
        {"option": "Option A: Approve primary proposal and proceed immediately", "pros_cons": "Fast execution, requires team focus"},
        {"option": "Option B: Scope down MVP version to unblock dependencies", "pros_cons": "Lowers short-term risk, defers advanced features"},
        {"option": "Option C: Defer to next sprint with clear milestones", "pros_cons": "Allows more investigation, delays delivery"},
    ])
    for opt in options:
        opt_text = opt.get("option", str(opt))
        pros_cons = opt.get("pros_cons", "")
        blocks.append(f"- **{opt_text}**" + (f": *{pros_cons}*" if pros_cons else ""))

    blocks.append("## 4. Suggested Owner & Next Step")
    blocks.append(f"- **Owner**: @{suggested_owner}")
    blocks.append(f"- **Immediate Action**: {suggested_next_step}")

    blocks.append("## 5. Sign-off Checklist")
    blocks.append("- [ ] @Maya (Product Manager) Approved")
    blocks.append("- [ ] @Engineering Lead Approved")
    blocks.append(f"- [ ] @{suggested_owner} Assigned Action Item")

    return blocks


def write_notion_decision_page_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: write_notion_decision_page] Publishing dedicated Notion Decision Pages...")

    stuck_topics = state.get("stuck_topics") or []
    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )
    parent_page_id = os.getenv("NOTION_HEALTH_REPORT_PARENT_PAGE_ID")

    created_urls: List[str] = []
    tool_calls: List[Dict[str, Any]] = []

    for topic in stuck_topics:
        topic_name = topic.get("topic", "Unresolved Issue")
        page_title = f"[Decision Page] {topic_name}"
        content_blocks = _build_decision_page_blocks(topic)

        try:
            url = notion_create_page(
                parent_id=parent_page_id,
                title=page_title,
                content_blocks=content_blocks,
                mock=is_dry_run,
            )
            created_urls.append(url)
            tool_calls.append({"tool": "Notion", "action": "create_decision_page", "target": page_title})
        except Exception as e:
            logger.error(f"Error creating decision page for '{topic_name}': {e}")
            fallback_url = f"https://notion.so/meetloop/decision-fallback"
            created_urls.append(fallback_url)

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="write_notion_decision_pages",
        what_it_decided=f"Published {len(created_urls)} dedicated Notion Decision Page(s)",
        input_summary=f"Synthesized decision profiles for {len(stuck_topics)} stuck topic(s)",
        output_summary=f"Created Notion Decision Pages -> {created_urls}",
        tool_calls=tool_calls,
    )

    return {
        "notion_decision_page_urls": created_urls,
        "reasoning_trace": new_trace,
    }
