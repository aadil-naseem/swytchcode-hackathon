"""
LangGraph StateGraph Definition for MeetLoop.

Routes execution between:
1. Audit Mode: Google Meet Ingestion -> Cross-Meeting Analysis -> Pattern & Stuck Topic Detection -> Notion Health Report & Decision Pages -> Gmail Digest -> Slack Pulse.
2. Brief Mode: Notion & Gmail Context Retrieval -> Pre-Meeting Brief Synthesis.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from backend.agent.state import ClearRoomState
from backend.agent.nodes import (
    classify_input_node,
    fetch_gmeet_transcript_node,
    analyze_meetings_node,
    extract_patterns_node,
    detect_stuck_topics_node,
    write_notion_report_node,
    write_notion_decision_page_node,
    send_gmail_digest_node,
    post_slack_pulse_node,
    search_notion_node,
    search_gmail_node,
    generate_brief_node,
)


def route_by_mode(state: ClearRoomState) -> Literal["fetch_gmeet_transcript", "search_notion"]:
    """Conditional edge router based on mode."""
    mode = state.get("mode", "audit")
    if mode == "brief":
        return "search_notion"
    return "fetch_gmeet_transcript"


def build_clearroom_graph():
    """Builds and compiles the MeetLoop StateGraph."""
    workflow = StateGraph(ClearRoomState)

    # Add all nodes
    workflow.add_node("classify_input", classify_input_node)
    
    # Audit Path Nodes
    workflow.add_node("fetch_gmeet_transcript", fetch_gmeet_transcript_node)
    workflow.add_node("analyze_meetings", analyze_meetings_node)
    workflow.add_node("extract_patterns", extract_patterns_node)
    workflow.add_node("detect_stuck_topics", detect_stuck_topics_node)
    workflow.add_node("write_notion_report", write_notion_report_node)
    workflow.add_node("write_notion_decision_page", write_notion_decision_page_node)
    workflow.add_node("send_gmail_digest", send_gmail_digest_node)
    workflow.add_node("post_slack_pulse", post_slack_pulse_node)

    # Brief Path Nodes
    workflow.add_node("search_notion", search_notion_node)
    workflow.add_node("search_gmail", search_gmail_node)
    workflow.add_node("generate_brief", generate_brief_node)

    # Edges
    workflow.add_edge(START, "classify_input")

    # Conditional Branch from classify_input
    workflow.add_conditional_edges(
        "classify_input",
        route_by_mode,
        {
            "fetch_gmeet_transcript": "fetch_gmeet_transcript",
            "search_notion": "search_notion",
        }
    )

    # Audit Flow Edges
    workflow.add_edge("fetch_gmeet_transcript", "analyze_meetings")
    workflow.add_edge("analyze_meetings", "extract_patterns")
    workflow.add_edge("extract_patterns", "detect_stuck_topics")
    workflow.add_edge("detect_stuck_topics", "write_notion_report")
    workflow.add_edge("write_notion_report", "write_notion_decision_page")
    workflow.add_edge("write_notion_decision_page", "send_gmail_digest")
    workflow.add_edge("send_gmail_digest", "post_slack_pulse")
    workflow.add_edge("post_slack_pulse", END)

    # Brief Flow Edges
    workflow.add_edge("search_notion", "search_gmail")
    workflow.add_edge("search_gmail", "generate_brief")
    workflow.add_edge("generate_brief", END)

    return workflow.compile()


# Compiled singleton instance
clearroom_agent = build_clearroom_graph()
