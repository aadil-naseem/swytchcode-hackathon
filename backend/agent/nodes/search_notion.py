"""
Phase 13 & 14 - Brief Mode: Search Notion Context Node.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools import notion_search_pages
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("clearroom.agent.search_notion")


def search_notion_node(state: ClearRoomState) -> Dict[str, Any]:
    topic = state.get("brief_topic") or state.get("prompt") or "General"
    print(f"[Node: search_notion] Searching Notion workspace for '{topic}'...")

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )

    try:
        results = notion_search_pages(query=topic, mock=is_dry_run)
    except Exception as e:
        logger.warning(f"Notion search failed: {e}")
        results = []

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="search_notion",
        what_it_decided=f"Retrieved {len(results)} Notion document(s) for '{topic}'",
        input_summary=f"Queried Notion for topic: '{topic}'",
        output_summary=(
            f"Found {len(results)} Notion page(s): "
            + (", ".join(f"'{r.get('title')}'" for r in results[:2]) if results else "No matches")
        ),
        tool_calls=[{"tool": "Notion", "action": "search_pages", "query": topic, "count": len(results)}],
    )

    return {
        "notion_search_results": results,
        "reasoning_trace": new_trace,
    }
