"""
Phase 13 & 14 - Brief Mode: Search Gmail Context Node.
"""

import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.tools import gmail_search_threads
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("clearroom.agent.search_gmail")


def search_gmail_node(state: ClearRoomState) -> Dict[str, Any]:
    topic = state.get("brief_topic") or state.get("prompt") or "General"
    print(f"[Node: search_gmail] Searching Gmail threads for '{topic}'...")

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or not os.getenv("SWYTCHCODE_API_KEY")
    )

    try:
        results = gmail_search_threads(query=topic, mock=is_dry_run)
    except Exception as e:
        logger.warning(f"Gmail search failed: {e}")
        results = []

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="search_gmail",
        what_it_decided=f"Retrieved {len(results)} Gmail thread(s) for '{topic}'",
        input_summary=f"Queried Gmail for topic: '{topic}'",
        output_summary=(
            f"Found {len(results)} email thread(s): "
            + (", ".join(f"'{r.get('subject')}'" for r in results[:2]) if results else "No matches")
        ),
        tool_calls=[{"tool": "Gmail", "action": "search_threads", "query": topic, "count": len(results)}],
    )

    return {
        "gmail_search_results": results,
        "reasoning_trace": new_trace,
    }
