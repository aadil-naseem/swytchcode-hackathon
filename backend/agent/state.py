"""
Shared LangGraph State Schema for MeetLoop.
Contract used across all nodes in the agent graph.
"""

from typing import Any, Dict, List, Optional, TypedDict


class ClearRoomState(TypedDict, total=False):
    # Input
    mode: str  # "audit" | "brief"
    prompt: Optional[str]  # Natural language input from user
    raw_input: Optional[str]  # Raw string input (either pasted notes or query)
    raw_meeting_notes: List[str]  # Audit mode: list of meeting transcripts/notes
    brief_topic: str  # Brief mode: topic/title to brief on

    # Google Meet Ingestion
    gmeet_meeting_code: Optional[str]  # Short alphanumeric Meet code (e.g. "abc-defg-hij")
    gmeet_date_range: Optional[List[str]]  # Optional [ISO_start, ISO_end]
    gmeet_transcript_fetched: Optional[bool]  # Ingestion success indicator

    # Audit mode working data
    parsed_meetings: List[Dict[str, Any]]  # Normalized per-meeting structure
    recurring_topics: List[Dict[str, Any]]  # Topics discussed across meetings
    decision_velocity: Dict[str, Any]  # Topics discussed vs decisions made
    commitment_load: Dict[str, Any]  # Person -> count/list of action items
    agenda_outcome_gaps: List[Dict[str, Any]]  # Planned vs resolved per meeting
    meeting_necessity_scores: Dict[str, Any]  # Necessity scores & async recommendations
    stuck_topics: List[Dict[str, Any]]  # [{topic, occurrences, blocking_reason, suggested_owner, suggested_next_step}]

    # Brief mode working data
    notion_search_results: List[Dict[str, Any]]
    gmail_search_results: List[Dict[str, Any]]
    brief_output: Dict[str, Any]

    # Outputs & side effects
    notion_report_url: Optional[str]
    notion_decision_page_urls: List[str]
    gmail_digest_sent: bool
    slack_pulse_sent: bool

    # Observability & audit trail
    reasoning_trace: List[Dict[str, Any]]  # Ordered log of {node, decision, input_summary, output_summary, timestamp}
    errors: List[Dict[str, Any]]
