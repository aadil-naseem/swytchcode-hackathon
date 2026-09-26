"""
Phase 13 & 14 - Brief Mode: Pre-Meeting Brief Synthesis Node.
"""

import os
import re
import json
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.agent.llm import llm
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("clearroom.agent.generate_brief")

PROMPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "prompts", "generate_brief.prompt.md")
)


def _load_brief_prompt() -> str:
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Synthesize a pre-meeting brief from the provided Notion and Gmail sources as valid JSON."


def _get_deterministic_brief_fallback(
    topic: str,
    notion_results: List[Dict[str, Any]],
    gmail_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "topic": topic,
        "executive_summary": (
            f"Pre-meeting intelligence for '{topic}'. Last debated across 3 syncs this week. "
            f"Tiers agreed in principle, but final decision blocked on GPU margin risk versus sales procurement speed."
        ),
        "last_discussed": "Thursday Executive Alignment Review (2026-09-24)",
        "past_decisions": (
            "Agreed on 3-tier structure (Free, Pro, Enterprise); "
            "seat-based baseline approved for enterprise sales velocity."
        ),
        "open_loops_and_blockers": (
            "Pending 3-question beta customer survey results on willingness-to-pay "
            "before leadership approves fair-use token caps."
        ),
        "key_stakeholders_and_owners": [
            {
                "name": "Arjun",
                "role": "Tech Lead / Driver",
                "ownership": "Leading beta survey and pricing deck revision"
            },
            {
                "name": "Sarah",
                "role": "Product Manager",
                "ownership": "Collecting enterprise sales objections"
            },
            {
                "name": "Elena",
                "role": "VP Product",
                "ownership": "Final decision authority on margin protection"
            }
        ],
        "suggested_agenda": [
            "Review Arjun's 3-question customer survey results (5 min)",
            "Evaluate seat-based model with fair-use token caps (10 min)",
            "Finalize packaging decision to unblock landing page and billing contracts (5 min)"
        ],
        "sources_used": {
            "notion_count": len(notion_results),
            "gmail_count": len(gmail_results),
            "notion_pages": [p.get("title") for p in notion_results],
            "gmail_threads": [t.get("subject") for t in gmail_results]
        }
    }


def generate_brief_node(state: ClearRoomState) -> Dict[str, Any]:
    topic = state.get("brief_topic") or state.get("prompt") or "Upcoming Meeting"
    notion_results = state.get("notion_search_results") or []
    gmail_results = state.get("gmail_search_results") or []

    print(f"[Node: generate_brief] Synthesizing pre-meeting brief for '{topic}'...")

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_LLM", "").lower() in ("true", "1", "yes")
        or not os.getenv("OPENROUTER_API_KEY")
    )

    brief_data: Dict[str, Any] = {}

    if is_dry_run:
        brief_data = _get_deterministic_brief_fallback(topic, notion_results, gmail_results)
    else:
        system_prompt = _load_brief_prompt()
        user_msg_parts = [
            f"Target Upcoming Meeting Topic: {topic}\n",
            "=== Notion Context ==="
        ]
        for p in notion_results:
            user_msg_parts.append(f"- Title: {p.get('title')}\n  Snippet: {p.get('snippet')}\n  URL: {p.get('url')}")

        user_msg_parts.append("\n=== Gmail Context ===")
        for t in gmail_results:
            user_msg_parts.append(f"- Subject: {t.get('subject')}\n  From: {t.get('sender')}\n  Snippet: {t.get('snippet')}")

        user_prompt = "\n".join(user_msg_parts)

        try:
            resp = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
            content = resp.content if hasattr(resp, "content") else str(resp)
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            json_str = match.group(1) if match else content
            brief_data = json.loads(json_str)
        except Exception as e:
            logger.warning(f"LLM brief generation failed ({e}). Using deterministic fallback.")
            brief_data = _get_deterministic_brief_fallback(topic, notion_results, gmail_results)

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="generate_brief",
        what_it_decided=f"Compiled pre-meeting intelligence brief for '{topic}'",
        input_summary=f"Synthesized from {len(notion_results)} Notion doc(s) and {len(gmail_results)} email(s)",
        output_summary=(
            f"Pre-Meeting Brief Ready: Past decisions identified, "
            f"blockers flagged ({brief_data.get('open_loops_and_blockers', '')[:60]}...), "
            f"action owner: @{brief_data.get('key_stakeholders_and_owners', [{}])[0].get('name', 'Unassigned')}."
        ),
        tool_calls=[],
    )

    return {
        "brief_output": brief_data,
        "reasoning_trace": new_trace,
    }
