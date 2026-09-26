"""
FastAPI Routes for MeetLoop Agent Backend.

Endpoints:
- POST /run: Executes the MeetLoop agent graph (Audit or Brief mode, supports manual notes or Google Meet code)
- GET /health: Liveness and status check
- GET /fixtures: Provides default sample meeting transcripts for 1-click demos
"""

import os
import glob
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.agent.graph import clearroom_agent
except ImportError:
    from agent.graph import clearroom_agent

router = APIRouter()

FIXTURES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
)


class RunRequest(BaseModel):
    mode: Optional[str] = Field(None, description="'audit' or 'brief'. If omitted, auto-classified from prompt.")
    prompt: Optional[str] = Field(None, description="Natural language user request (e.g., 'Brief me on Pricing Strategy')")
    raw_meeting_notes: Optional[Union[List[str], str]] = Field(None, description="Meeting transcripts for cross-meeting audit")
    gmeet_meeting_code: Optional[str] = Field(None, description="Google Meet code (e.g. 'abc-defg-hij') to fetch live transcript")
    gmeet_date_range: Optional[List[str]] = Field(None, description="Optional date range [start, end] for Meet conference records")
    brief_topic: Optional[str] = Field(None, description="Topic for pre-meeting briefing")
    dry_run: Optional[bool] = Field(None, description="Optional override to force dry-run mode")


class RunResponse(BaseModel):
    status: str
    mode: str
    prompt: Optional[str] = None
    brief_topic: Optional[str] = None
    gmeet_meeting_code: Optional[str] = None
    gmeet_transcript_fetched: Optional[bool] = None
    summary_insight: Optional[str] = None
    stuck_topics: List[Dict[str, Any]] = []
    commitment_load: Dict[str, Any] = {}
    meeting_necessity_scores: Dict[str, Any] = {}
    brief_output: Optional[Dict[str, Any]] = None
    notion_report_url: Optional[str] = None
    notion_decision_page_urls: List[str] = []
    gmail_digest_sent: bool = False
    slack_pulse_sent: bool = False
    reasoning_trace: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []


@router.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Liveness check and service metadata."""
    return {
        "status": "ok",
        "service": "MeetLoop AI Meeting Auditor",
        "version": "1.0.0",
        "integrations": ["Notion", "Gmail", "Slack", "Google Meet"],
        "llm_provider": "OpenRouter",
    }


@router.get("/fixtures", tags=["Demo Data"])
async def get_demo_fixtures() -> Dict[str, Any]:
    """Returns sample fixture transcripts for 1-click frontend demos."""
    fixture_files = sorted(glob.glob(os.path.join(FIXTURES_DIR, "*.txt")))
    fixtures = []
    for fpath in fixture_files:
        filename = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            fixtures.append({
                "filename": filename,
                "title": filename.replace(".txt", "").replace("_", " ").title(),
                "content": content,
            })
    return {
        "count": len(fixtures),
        "fixtures": fixtures,
        "sample_brief_topics": [
            "Pricing Strategy",
            "Infrastructure Migration to GPU Clusters",
            "Tailwind Design System Tokens"
        ],
        "sample_gmeet_codes": [
            "abc-defg-hij",
            "pulseboard-sync",
            "weekly-eng-retro"
        ]
    }


@router.post("/run", response_model=RunResponse, tags=["Agent Execution"])
async def run_agent(req: RunRequest) -> RunResponse:
    """
    Executes the MeetLoop agent graph.
    Routes to Audit Mode or Brief Mode and returns state + reasoning trace.
    """
    if req.dry_run is not None:
        os.environ["DRY_RUN"] = "true" if req.dry_run else "false"

    # If raw_meeting_notes and gmeet_meeting_code not provided in audit mode or empty, load default fixtures
    raw_notes = req.raw_meeting_notes
    if (req.mode == "audit" or not req.prompt) and not raw_notes and not req.gmeet_meeting_code:
        fixture_files = sorted(glob.glob(os.path.join(FIXTURES_DIR, "*.txt")))
        loaded_notes = []
        for fpath in fixture_files:
            with open(fpath, "r", encoding="utf-8") as f:
                loaded_notes.append(f.read())
        raw_notes = loaded_notes

    # Prepare initial state
    initial_state = {
        "mode": req.mode or "",
        "prompt": req.prompt or "",
        "raw_meeting_notes": raw_notes if isinstance(raw_notes, list) else ([raw_notes] if raw_notes else []),
        "gmeet_meeting_code": req.gmeet_meeting_code or "",
        "gmeet_date_range": req.gmeet_date_range or [],
        "brief_topic": req.brief_topic or "",
        "reasoning_trace": [],
        "errors": [],
    }

    try:
        final_state = clearroom_agent.invoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MeetLoop agent execution failed: {str(e)}",
        )

    # Derive high-level summary insight for UI focal point
    mode = final_state.get("mode", "audit")
    summary_insight = ""
    if mode == "audit":
        stuck = final_state.get("stuck_topics") or []
        stuck_str = f"{len(stuck)} topic(s) stuck" if stuck else "0 stuck topics"
        top_overload = final_state.get("commitment_load", {}).get("overloaded_people", [])
        overload_str = f", {top_overload[0]['name']} is overloaded ({top_overload[0]['action_item_count']} tasks)" if top_overload else ""
        gmeet_str = " (Google Meet transcript ingested)" if final_state.get("gmeet_transcript_fetched") else ""
        summary_insight = f"Audit complete{gmeet_str}: {stuck_str}{overload_str}. Reports published to Notion, Gmail digest sent, Slack pulse broadcast."
    else:
        brief = final_state.get("brief_output") or {}
        summary_insight = brief.get("executive_summary") or f"Pre-meeting brief prepared for '{final_state.get('brief_topic')}'."

    return RunResponse(
        status="success",
        mode=mode,
        prompt=req.prompt,
        brief_topic=final_state.get("brief_topic"),
        gmeet_meeting_code=final_state.get("gmeet_meeting_code"),
        gmeet_transcript_fetched=final_state.get("gmeet_transcript_fetched"),
        summary_insight=summary_insight,
        stuck_topics=final_state.get("stuck_topics", []),
        commitment_load=final_state.get("commitment_load", {}),
        meeting_necessity_scores=final_state.get("meeting_necessity_scores", {}),
        brief_output=final_state.get("brief_output"),
        notion_report_url=final_state.get("notion_report_url"),
        notion_decision_page_urls=final_state.get("notion_decision_page_urls", []),
        gmail_digest_sent=final_state.get("gmail_digest_sent", False),
        slack_pulse_sent=final_state.get("slack_pulse_sent", False),
        reasoning_trace=final_state.get("reasoning_trace", []),
        errors=final_state.get("errors", []),
    )
