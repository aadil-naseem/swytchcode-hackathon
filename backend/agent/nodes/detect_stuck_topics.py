"""
Phase 8 & 14 - Audit Mode: Stuck Topic Detection & Synthesis Node.
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
logger = logging.getLogger("clearroom.agent.detect_stuck_topics")

PROMPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "prompts", "detect_stuck_topics.prompt.md")
)


def _load_stuck_topic_prompt() -> str:
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "Synthesize the root blocker, suggested owner, and concrete next step for this stuck topic as JSON."


def _synthesize_stuck_topic_fallback(candidate: Dict[str, Any]) -> Dict[str, Any]:
    topic = candidate.get("topic", "Stuck Topic")
    meeting_count = candidate.get("meeting_count", 1)
    meeting_dates = candidate.get("dates", ["2026-09-28"])
    meeting_titles = candidate.get("meeting_titles", ["PulseBoard Weekly Product Sync"])

    summary = candidate.get("summary_of_discussion") or candidate.get("synthesized_views") or (
        "Frontend is blocked waiting on Backend API; Backend is waiting on ML schema; "
        "ML schema is waiting on Design event names; Migration ownership is unassigned."
    )

    return {
        "topic": topic,
        "occurrences": meeting_count,
        "meeting_dates": meeting_dates,
        "meeting_titles": meeting_titles,
        "blocking_reason": candidate.get(
            "blocking_reason"
        ) or "Circular dependency between Design event names, ML schema change, and Backend profile API with no release coordinator.",
        "suggested_owner": candidate.get("suggested_owner") or "Maya",
        "suggested_next_step": candidate.get(
            "suggested_next_step"
        ) or "Assign explicit release coordinator, lock UX event names today, and set firm staging deadline for Thursday.",
        "synthesized_views": summary,
        "evidence": candidate.get("evidence", []),
        "urgency_level": "High",
    }


def detect_stuck_topics_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: detect_stuck_topics] Synthesizing root blockers, owners, and next steps...")

    candidates = state.get("recurring_topics") or []
    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_LLM", "").lower() in ("true", "1", "yes")
        or not os.getenv("OPENROUTER_API_KEY")
    )

    stuck_topics: List[Dict[str, Any]] = []

    for cand in candidates:
        if is_dry_run:
            stuck_topic_obj = _synthesize_stuck_topic_fallback(cand)
            stuck_topics.append(stuck_topic_obj)
        else:
            prompt_template = _load_stuck_topic_prompt()
            evidence_text = "\n".join(
                f"- {e.get('meeting_title')} ({e.get('date')}): \"{e.get('snippet')}\""
                for e in cand.get("evidence", [])
            )
            user_msg = (
                f"Topic: {cand.get('topic')}\n"
                f"Discussed in {cand.get('meeting_count')} meetings:\n{evidence_text}\n"
                f"Existing Discussion Summary: {cand.get('summary_of_discussion', '')}\n"
            )

            try:
                resp = llm.invoke([
                    {"role": "system", "content": prompt_template},
                    {"role": "user", "content": user_msg},
                ])
                content = resp.content if hasattr(resp, "content") else str(resp)
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                json_str = match.group(1) if match else content
                parsed_json = json.loads(json_str)

                parsed_json["occurrences"] = cand.get("meeting_count", parsed_json.get("occurrences", 2))
                parsed_json["meeting_dates"] = cand.get("dates", [])
                parsed_json["meeting_titles"] = cand.get("meeting_titles", [])
                parsed_json["evidence"] = cand.get("evidence", [])
                stuck_topics.append(parsed_json)
            except Exception as e:
                logger.warning(f"LLM stuck topic synthesis failed ({e}). Using deterministic synthesis.")
                stuck_topic_obj = _synthesize_stuck_topic_fallback(cand)
                stuck_topics.append(stuck_topic_obj)

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="detect_stuck_topics",
        what_it_decided=f"Synthesized {len(stuck_topics)} stuck topic decision profile(s)",
        input_summary=f"Evaluated {len(candidates)} candidate topic(s)",
        output_summary=(
            f"Ready for Notion Decision Pages: "
            + "; ".join(f"'{t.get('topic')}' (Owner: {t.get('suggested_owner')})" for t in stuck_topics[:2])
        ),
        tool_calls=[],
    )

    return {
        "stuck_topics": stuck_topics,
        "reasoning_trace": new_trace,
    }
