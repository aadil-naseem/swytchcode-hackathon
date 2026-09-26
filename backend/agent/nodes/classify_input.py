"""
Phase 13 & 14 - Classifies incoming requests into 'audit' or 'brief' mode
and extracts target topic keywords for pre-meeting intelligence.
"""

import re
from typing import Dict, Any
from backend.agent.state import ClearRoomState
from backend.observability import append_trace_step


def _extract_brief_topic_from_prompt(prompt: str) -> str:
    """Extracts target topic from prompts like 'I have a meeting tomorrow about X — brief me'."""
    prompt = prompt.strip()
    
    m1 = re.search(r"(?i)about\s+([^\-—–]+)\s*[-—–]+\s*brief", prompt)
    if m1:
        return m1.group(1).strip()

    m2 = re.search(r"(?i)brief\s+me\s+(?:on|about|for)\s+([^\.\n]+)", prompt)
    if m2:
        return m2.group(1).strip()

    m3 = re.search(r"(?i)prep\s+(?:me\s+)?(?:for|on|about)\s+([^\.\n]+)", prompt)
    if m3:
        return m3.group(1).strip()

    cleaned = re.sub(r"(?i)\b(brief me|brief|prep|tomorrow|meeting)\b", "", prompt)
    cleaned = re.sub(r"[-—–:]+", "", cleaned).strip()
    return cleaned or "Pricing Strategy"


def classify_input_node(state: ClearRoomState) -> Dict[str, Any]:
    """
    Determines whether the user is requesting a cross-meeting 'audit' or a pre-meeting 'brief'.
    """
    print("[Node: classify_input] Classifying request intent and routing...")

    mode = state.get("mode")
    prompt = state.get("prompt") or ""
    brief_topic = state.get("brief_topic") or ""

    if not mode:
        prompt_lower = prompt.lower()
        if (
            "brief" in prompt_lower
            or "prep" in prompt_lower
            or "tomorrow" in prompt_lower
            or "upcoming" in prompt_lower
            or bool(brief_topic)
        ):
            mode = "brief"
        else:
            mode = "audit"

    if mode == "brief" and not brief_topic and prompt:
        brief_topic = _extract_brief_topic_from_prompt(prompt)

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="classify_input",
        what_it_decided=f"Routed to {mode.upper()} mode" + (f" (Topic: '{brief_topic}')" if brief_topic else ""),
        input_summary=f"Received prompt: '{prompt[:80]}...' " if prompt else f"Explicit mode='{mode}'",
        output_summary=f"Selected mode: '{mode}'" + (f", target topic: '{brief_topic}'" if brief_topic else ""),
        tool_calls=[],
    )

    return {
        "mode": mode,
        "brief_topic": brief_topic,
        "reasoning_trace": new_trace,
    }
