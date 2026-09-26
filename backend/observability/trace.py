"""
Agent Reasoning and Audit Trail Logger.
Provides structured tracking of agent decisions, tool execution, and state transitions
for live demo observability and judging visualization.
"""

import datetime
from typing import Any, Dict, List, Optional


def append_trace_step(
    existing_trace: Optional[List[Dict[str, Any]]],
    node_name: str,
    what_it_decided: str,
    input_summary: str = "",
    output_summary: str = "",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    status: str = "success",
) -> List[Dict[str, Any]]:
    """
    Appends a structured reasoning step to the trace list.
    """
    trace_list = list(existing_trace or [])
    step_num = len(trace_list) + 1

    entry = {
        "step": step_num,
        "node": node_name,
        "node_name": node_name,
        "decision": what_it_decided,
        "what_it_decided": what_it_decided,
        "input_summary": input_summary,
        "output_summary": output_summary,
        "tool_calls": tool_calls or [],
        "status": status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    trace_list.append(entry)
    return trace_list


def format_trace_for_display(trace_list: List[Dict[str, Any]]) -> str:
    """Formats the trace into a human-readable live timeline."""
    lines = ["=== MeetLoop Live Agent Reasoning Trace ==="]
    for step in trace_list:
        status_icon = "[OK]" if step.get("status") == "success" else "[ERR]"
        lines.append(
            f"Step {step.get('step', 1)} | {status_icon} Node: [{step.get('node')}]\n"
            f"  • Decision: {step.get('decision')}\n"
            f"  • Output: {step.get('output_summary')}"
        )
        if step.get("tool_calls"):
            for tc in step["tool_calls"]:
                lines.append(f"    -> Tool: {tc.get('tool')} ({tc.get('action')})")
    return "\n".join(lines)
