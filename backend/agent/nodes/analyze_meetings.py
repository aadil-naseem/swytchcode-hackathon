"""
Phase 6, 7 & 14 - Audit Mode: Data Ingestion, Preprocessing & Cross-Meeting Reasoning Node.
"""

import os
import re
import json
import logging
import datetime
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

from backend.agent.state import ClearRoomState
from backend.agent.llm import llm
from backend.observability import append_trace_step

load_dotenv()
logger = logging.getLogger("clearroom.agent.analyze_meetings")

PROMPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "prompts", "analyze_meetings.prompt.md")
)


def _load_system_prompt() -> str:
    if os.path.exists(PROMPT_PATH):
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "You are ClearRoom, an AI Meeting Auditor analyzing cross-meeting patterns. Return valid JSON."


def _clean_transcript_text(text: str) -> str:
    cleaned = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\]", "", text)
    cleaned = re.sub(r"\(\d{1,2}:\d{2}(?::\d{2})?\)", "", cleaned)
    cleaned = re.sub(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b", "", cleaned)
    cleaned = re.sub(r"(?i)^(transcript|recording started|recording ended)\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_meeting_metadata(raw_text: str, default_index: int) -> Dict[str, Any]:
    title = f"Meeting {default_index}"
    date = datetime.date.today().isoformat()
    participants: List[str] = []

    lines = raw_text.strip().splitlines()
    body_lines = []

    # Check if first non-empty line is "MEETING REPORT" style header
    first_nonempty = next((l.strip() for l in lines if l.strip()), "")
    if re.match(r"(?i)^meeting\s+report\s*$", first_nonempty):
        title = "Meeting Report"

    in_attendees_block = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            in_attendees_block = False
            body_lines.append(line)
            continue

        title_match = re.match(r"(?i)^(?:title|subject)\s*:\s*(.+)$", stripped)
        meeting_title_match = re.match(r"(?i)^meeting\s*:\s*(.+)$", stripped)
        date_match = re.match(r"(?i)^(?:date|time)\s*:\s*(.+)$", stripped)
        participants_match = re.match(r"(?i)^(?:participants|attendees|present)\s*:\s*(.+)$", stripped)
        attendees_header_match = re.match(r"(?i)^(?:participants|attendees|present)\s*[:\-–]?\s*$", stripped)
        agenda_match = re.match(r"(?i)^agenda\s*:\s*(.+)$", stripped)

        if title_match:
            title = title_match.group(1).strip()
            in_attendees_block = False
        elif meeting_title_match:
            title = meeting_title_match.group(1).strip()
            in_attendees_block = False
        elif date_match:
            date = date_match.group(1).strip()
            in_attendees_block = False
        elif participants_match:
            # Attendees listed inline: "Attendees: Alice, Bob, Carol"
            parts = participants_match.group(1).split(",")
            for p in parts:
                p_clean = re.sub(r"\s*\(.*?\)", "", p).strip()
                if p_clean:
                    participants.append(p_clean)
            in_attendees_block = True  # might continue with bullets on next lines
        elif attendees_header_match:
            # Attendees block starts on next lines
            in_attendees_block = True
        elif agenda_match and title == f"Meeting {default_index}":
            # Use agenda as title if no better title found
            title = agenda_match.group(1).strip()[:60]
            in_attendees_block = False
            body_lines.append(line)
        elif in_attendees_block:
            # Handle bullet points: "• Name", "- Name", "* Name", "Name Lastname"
            bullet_match = re.match(r"^[•\-\*\–]\s*(.+)$", stripped)
            if bullet_match:
                name = re.sub(r"\s*\(.*?\)", "", bullet_match.group(1)).strip()
                if name and len(name.split()) <= 4:
                    participants.append(name)
            elif re.match(r"^[A-Z]", stripped) and "," in stripped:
                # Comma-separated list
                for p in stripped.split(","):
                    p_clean = re.sub(r"\s*\(.*?\)", "", p).strip()
                    if p_clean:
                        participants.append(p_clean)
                in_attendees_block = False
            elif re.match(r"(?i)^(conducted by|platform|time|date|agenda|meeting summary)", stripped):
                in_attendees_block = False
                body_lines.append(line)
            else:
                # Single name on a line
                name = re.sub(r"\s*\(.*?\)", "", stripped).strip()
                if name and len(name.split()) <= 4 and re.match(r"^[A-Za-z]", name):
                    participants.append(name)
        else:
            body_lines.append(line)

    clean_content = _clean_transcript_text("\n".join(body_lines))

    if not participants:
        speaker_matches = re.findall(r"(?m)^([A-Z][a-zA-Z\s]{1,20})\s*:", clean_content)
        unique_speakers = []
        for s in speaker_matches:
            s_clean = s.strip()
            if s_clean and s_clean not in unique_speakers and len(s_clean.split()) <= 3:
                unique_speakers.append(s_clean)
        participants = unique_speakers

    return {
        "index": default_index,
        "title": title,
        "date": date,
        "participants": participants,
        "clean_transcript": clean_content,
        "raw_transcript": raw_text.strip(),
    }



def _split_text_into_chunks(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []

    if re.search(r"(?m)^[-=]{3,}\s*$", text):
        parts = re.split(r"(?m)^[-=]{3,}\s*$", text)
        return [p.strip() for p in parts if p.strip()]

    title_matches = list(re.finditer(r"(?m)^(?:Title|Meeting\s+\d+)\s*:", text))
    if len(title_matches) > 1:
        chunks = []
        for i, match in enumerate(title_matches):
            start = match.start()
            end = title_matches[i + 1].start() if i + 1 < len(title_matches) else len(text)
            chunks.append(text[start:end].strip())
        return chunks

    return [text]


def _split_raw_input_into_meetings(raw_input: Union[List[str], str]) -> List[str]:
    if isinstance(raw_input, str):
        return _split_text_into_chunks(raw_input)

    if isinstance(raw_input, list):
        all_chunks = []
        for item in raw_input:
            if isinstance(item, str) and item.strip():
                sub_chunks = _split_text_into_chunks(item)
                all_chunks.extend(sub_chunks)
        return all_chunks

    return []


def _extract_json_from_llm_response(text: str) -> Dict[str, Any]:
    """Robustly extracts and parses JSON from model output, handling thought tags and markdown."""
    text = text.strip()
    # Strip <think>...</think> reasoning blocks if model emitted them
    text = re.sub(r"(?s)<think>.*?</think>", "", text).strip()
    
    # Check for ```json ... ``` code fence
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
        
    # Check for outermost JSON object braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_candidate = text[first_brace:last_brace + 1]
        return json.loads(json_candidate)

    return json.loads(text)


def _extract_attendees_from_meetings(parsed_meetings: List[Dict[str, Any]]) -> List[str]:
    """Dynamically extract attendee names from parsed meeting data."""
    all_participants = []
    for m in parsed_meetings:
        for p in m.get("participants", []):
            if p and p not in all_participants:
                all_participants.append(p)
    return all_participants


def _extract_action_items_from_text(text: str) -> List[str]:
    """Heuristically find action items in meeting text."""
    action_patterns = [
        r"(?i)(?:will|shall|should|must|to)\s+([A-Za-z].{5,60}?)(?:\.|,|\n|$)",
        r"(?i)(?:action item|next step|follow.?up|todo|task)s?\s*:\s*([A-Za-z].{5,80}?)(?:\.|,|\n|$)",
        r"(?i)([A-Z][a-z]+)\s+(?:will|to)\s+([a-z].{5,60}?)(?:\.|,|\n|$)",
    ]
    items = []
    for pattern in action_patterns:
        matches = re.findall(pattern, text)
        for m in matches[:5]:
            item_text = m if isinstance(m, str) else " ".join(m)
            item_text = item_text.strip()
            if len(item_text) > 8 and item_text not in items:
                items.append(item_text)
    return items[:10]


def _get_deterministic_fixture_analysis(parsed_meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Dynamically analyze the actual transcript content instead of returning hardcoded fixture data.
    This ensures the fallback is always relevant to the provided transcript.
    """
    full_text = " ".join(m.get("clean_transcript", "") for m in parsed_meetings)
    full_text_lower = full_text.lower()

    # Gather real attendees from the parsed meetings
    all_attendees = _extract_attendees_from_meetings(parsed_meetings)

    # Compute action items dynamically from the actual text
    action_items = _extract_action_items_from_text(full_text)

    # Compute a simple workload distribution across known attendees
    counts_by_person: Dict[str, int] = {}
    for attendee in all_attendees:
        name_lower = attendee.lower()
        # Count mentions of the attendee name in transcript as a proxy for involvement/ownership
        count = full_text_lower.count(name_lower)
        counts_by_person[attendee] = min(count // 3, 5)  # normalize

    overloaded_people = []
    total_tasks = sum(counts_by_person.values()) or 1
    for name, cnt in sorted(counts_by_person.items(), key=lambda x: x[1], reverse=True):
        if cnt > 0 and (cnt / total_tasks) > 0.35:
            overloaded_people.append({
                "name": name,
                "action_item_count": cnt,
                "percentage_of_all_tasks": round((cnt / total_tasks) * 100, 1),
                "assessment": f"{name} appears most frequently in the transcript and may be carrying a disproportionate share of the discussion and action items.",
                "action_items": action_items[:3],
            })

    # Build a generic stuck topic from the real meeting content
    meeting_titles = [m.get("title", f"Meeting {m.get('index', 1)}") for m in parsed_meetings]
    meeting_dates  = [m.get("date",  "") for m in parsed_meetings]

    # Try to find a topic from the transcript title or content
    first_meeting = parsed_meetings[0] if parsed_meetings else {}
    main_topic = first_meeting.get("title", "Meeting Agenda")
    top_attendee = all_attendees[0] if all_attendees else "Unassigned"

    recurring_topics = [
        {
            "topic": main_topic,
            "meeting_count": len(parsed_meetings),
            "meeting_titles": meeting_titles,
            "dates": meeting_dates,
            "is_stuck": True,
            "status": "unresolved",
            "summary_of_discussion": (
                f"This meeting covered '{main_topic}'. "
                f"Across {len(parsed_meetings)} meeting(s) with {len(all_attendees)} attendee(s), "
                "some items may require follow-up to reach closure."
            ),
            "blocking_reason": "Full AI synthesis unavailable — deterministic analysis indicates follow-up required to close open items from this meeting.",
            "suggested_owner": top_attendee,
            "suggested_next_step": "Schedule a brief follow-up sync to assign owners to any open action items and set firm deadlines.",
        }
    ]

    return {
        "summary": {
            "total_meetings_analyzed": len(parsed_meetings),
            "total_topics_discussed": max(len(parsed_meetings), 1),
            "total_decisions_made": 0,
            "decision_velocity_score": "Pending full AI analysis",
            "executive_headline": (
                f"MeetLoop analyzed {len(parsed_meetings)} meeting(s) with {len(all_attendees)} attendee(s). "
                f"Primary meeting: '{main_topic}'. Follow-up review recommended."
            ),
        },
        "recurring_topics": recurring_topics,
        "decision_velocity": {
            "total_topics_opened": len(parsed_meetings),
            "total_decisions_finalized": 0,
            "overall_velocity_rate": 0.5,
            "status": "pending_review",
            "insights": "LLM analysis unavailable. Deterministic fallback used. Core meeting data captured.",
        },
        "commitment_load": {
            "counts_by_person": counts_by_person,
            "overloaded_people": overloaded_people,
            "balanced_people": [n for n in list(counts_by_person.keys()) if not any(o["name"] == n for o in overloaded_people)],
        },
        "agenda_outcome_gaps": [
            {
                "meeting_index": m.get("index", i + 1),
                "meeting_title": m.get("title", f"Meeting {i+1}"),
                "date": m.get("date", ""),
                "topics_opened": 1,
                "topics_resolved": 0,
                "resolution_rate": 0.0,
                "unresolved_topics": [m.get("title", "Agenda items")],
                "gap_notes": "AI synthesis unavailable. Review transcript for unresolved items.",
            }
            for i, m in enumerate(parsed_meetings)
        ],
        "meeting_necessity_scores": {
            m.get("title", f"Meeting {i+1}"): {
                "necessity_score": 7,
                "recommendation": "Keep as Live Sync",
                "reasoning": "Meeting importance could not be fully scored without AI analysis.",
            }
            for i, m in enumerate(parsed_meetings)
        },
    }


# NOTE: Legacy hardcoded fixture data has been removed. The dynamic analysis above
# now always operates on the real transcript content provided by the user.

def _pulseboard_hardcoded_check(parsed_meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy: kept for reference only — no longer called."""
    full_text = " ".join(m.get("clean_transcript", "") for m in parsed_meetings).lower()

    if "pulseboard" in full_text or "onboarding redesign" in full_text or "daniel" in full_text or "sofia" in full_text:
        return {
            "summary": {
                "total_meetings_analyzed": len(parsed_meetings),
                "total_topics_discussed": 4,
                "total_decisions_made": 1,
                "decision_velocity_score": "25% (Low - severe cross-functional deadlock)",
                "executive_headline": "Onboarding redesign release blocked by circular dependencies between ML event schema, Backend profile API, and Design naming. Critical execution & release coordination unowned."
            },
            "recurring_topics": [
                {
                    "topic": "Onboarding Redesign Release & Schema Migration",
                    "meeting_count": 1,
                    "meeting_titles": [m["title"] for m in parsed_meetings],
                    "dates": [m["date"] for m in parsed_meetings],
                    "is_stuck": True,
                    "status": "unresolved",
                    "summary_of_discussion": (
                        "Frontend ready but waiting on Backend profile API. Backend ready but waiting on ML event schema. "
                        "ML schema waiting on Designer UX event names (which Designer thought were already finalized Friday). "
                        "Arjun refused to own schema migration without final schema. No release coordinator assigned."
                    ),
                    "blocking_reason": "Circular blocker loop: Design event naming -> ML schema update -> Backend Profile API -> Frontend staging release. No owner assigned for schema migration or release coordination.",
                    "suggested_owner": "Maya",
                    "suggested_next_step": "Hold 10-min immediate unblocking sync: lock UX event names with Riya/Daniel by 2 PM, assign Arjun explicit migration ownership, lock Thursday staging target."
                },
                {
                    "topic": "Analytics Instrumentation & Duplicate Events vs Shipping Staging",
                    "meeting_count": 1,
                    "meeting_titles": [m["title"] for m in parsed_meetings],
                    "dates": [m["date"] for m in parsed_meetings],
                    "is_stuck": True,
                    "status": "unresolved",
                    "summary_of_discussion": "Debated whether to block staging release until analytics duplicate event issue is fixed. Ended with no clear decision.",
                    "blocking_reason": "Conflict between PM desire to ship to staging vs ML preference for clean single-migration analytics.",
                    "suggested_owner": "Daniel",
                    "suggested_next_step": "Instrument baseline analytics in staging first, run A/B test setup in parallel for Friday."
                }
            ],
            "decision_velocity": {
                "total_topics_opened": 4,
                "total_decisions_finalized": 1,
                "overall_velocity_rate": 0.25,
                "status": "critical_bottleneck",
                "insights": "Only 1 decision finalized (Daniel & Riya to post event names). Zero decisions on release coordination, migration ownership, or analytics timing."
            },
            "commitment_load": {
                "counts_by_person": {
                    "Daniel": 3,
                    "Arjun": 2,
                    "Riya": 1,
                    "Sofia": 1,
                    "Maya": 0
                },
                "overloaded_people": [
                    {
                        "name": "Daniel",
                        "action_item_count": 3,
                        "percentage_of_all_tasks": 42.8,
                        "assessment": "High dependency load: responsible for event schema, analytics validation, and A/B test spike.",
                        "action_items": [
                            "Finalize event names list with Riya",
                            "Confirm user-event schema for backend",
                            "Prepare A/B testing infrastructure for Friday"
                        ]
                    }
                ],
                "unowned_critical_areas": [
                    "Schema Migration Execution (Arjun declined ownership without final schema; unassigned)",
                    "Overall Staging Release Coordination (Unassigned)"
                ],
                "balanced_people": ["Arjun", "Sofia", "Riya", "Maya"]
            },
            "agenda_outcome_gaps": [
                {
                    "meeting_index": 1,
                    "meeting_title": "PulseBoard Weekly Product Sync",
                    "date": "2026-09-28",
                    "topics_opened": 4,
                    "topics_resolved": 1,
                    "resolution_rate": 0.25,
                    "unresolved_topics": ["Schema Migration Ownership", "Overall Release Coordinator", "Analytics Fix vs Staging Release Priority"],
                    "gap_notes": "48-minute meeting spent significant time re-litigating event naming that Designer thought was already approved last Friday."
                }
            ],
            "meeting_necessity_scores": {
                "PulseBoard Weekly Product Sync": {
                    "necessity_score": 4,
                    "recommendation": "Shift Event Naming & Status to Async",
                    "reasoning": "48-minute sync resulted in 1 minor decision. Event naming review should have been an async Figma/Slack thread prior to the meeting."
                }
            }
        }

    # Default pricing test fixture
    pricing_count = sum(1 for m in parsed_meetings if "pricing" in m.get("clean_transcript", "").lower())
    return {
        "summary": {
            "total_meetings_analyzed": len(parsed_meetings),
            "total_topics_discussed": 5,
            "total_decisions_made": 4,
            "decision_velocity_score": "20% in Strategy (Low), 100% in Retro (High)",
            "executive_headline": f"Pricing Strategy stalled across {pricing_count} meetings with 0 decisions; Arjun holds 70% of team action items."
        },
        "recurring_topics": [
            {
                "topic": "Pricing Strategy (Seat vs Usage-based)",
                "meeting_count": pricing_count,
                "meeting_titles": [m["title"] for m in parsed_meetings if "pricing" in m.get("clean_transcript", "").lower()],
                "dates": [m["date"] for m in parsed_meetings if "pricing" in m.get("clean_transcript", "").lower()],
                "is_stuck": True,
                "status": "unresolved",
                "summary_of_discussion": "Discussed seat-based ($25-30/seat) vs usage-based metering. Blocked by conflicting sales preferences and lack of executive decision.",
                "blocking_reason": "No consensus on seat vs usage metric and margin impact of GPU tokens.",
                "suggested_owner": "Arjun",
                "suggested_next_step": "Run 3-question beta customer survey and present fixed tier proposal on Monday."
            }
        ],
        "decision_velocity": {
            "total_topics_opened": 5,
            "total_decisions_finalized": 4,
            "overall_velocity_rate": 0.8,
            "standup_velocity_rate": 0.0,
            "retro_velocity_rate": 1.0,
            "status": "bifurcated",
            "insights": "Tuesday standup resolved 0 of 2 opened topics. Friday retro resolved 4 of 4 topics."
        },
        "commitment_load": {
            "counts_by_person": {
                "Arjun": 7,
                "Sarah": 1,
                "Priya": 2,
                "David": 1
            },
            "overloaded_people": [
                {
                    "name": "Arjun",
                    "action_item_count": 7,
                    "percentage_of_all_tasks": 63.6,
                    "assessment": "Severe overload: assigned majority of competitor research, financial spreadsheets, sync scheduling, and survey execution.",
                    "action_items": [
                        "Research competitor tier models",
                        "Draft preliminary pricing document",
                        "Set up call with sales leadership",
                        "Build financial model spreadsheet",
                        "Schedule alignment sync with VP Product",
                        "Send 3-question pricing survey to beta partners",
                        "Revise executive pricing deck"
                    ]
                }
            ],
            "balanced_people": ["Priya", "Sarah", "David"]
        },
        "agenda_outcome_gaps": [
            {
                "meeting_index": 1,
                "meeting_title": "Tuesday Engineering & Product Standup",
                "date": "2026-09-22",
                "topics_opened": 2,
                "topics_resolved": 0,
                "resolution_rate": 0.0,
                "unresolved_topics": ["Pricing Strategy", "Notion Webhook Handlers"],
                "gap_notes": "Standup drifted into unresolved strategy discussion; 0 decisions reached."
            },
            {
                "meeting_index": 4,
                "meeting_title": "Friday Sprint 14 Retrospective & Planning",
                "date": "2026-09-25",
                "topics_opened": 4,
                "topics_resolved": 4,
                "resolution_rate": 1.0,
                "unresolved_topics": [],
                "gap_notes": "High-velocity execution: 4 of 4 topics resolved cleanly with owners and deadlines."
            }
        ],
        "meeting_necessity_scores": {
            "Tuesday Engineering & Product Standup": {
                "necessity_score": 2,
                "recommendation": "Convert to Async",
                "reasoning": "0 decisions reached, 3 action items dumped on 1 person. Should be an async Slack standup."
            },
            "Wednesday Product Strategy Sync": {
                "necessity_score": 4,
                "recommendation": "Re-structure with Pre-reads",
                "reasoning": "Re-opened Pricing without required financial model ready."
            },
            "Thursday Executive Alignment Review": {
                "necessity_score": 6,
                "recommendation": "Keep but Require Decision Deadlines",
                "reasoning": "High leadership presence but deferred decision pending partner survey."
            },
            "Friday Sprint 14 Retrospective & Planning": {
                "necessity_score": 10,
                "recommendation": "Keep as Live Sync",
                "reasoning": "Highly efficient: 4 decisions finalized in 15 minutes."
            }
        }
    }


def analyze_meetings_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: analyze_meetings] Parsing notes and performing cross-meeting analysis...")
    
    raw_input = state.get("raw_meeting_notes") or state.get("prompt") or []
    meeting_chunks = _split_raw_input_into_meetings(raw_input)
    
    parsed_meetings: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(meeting_chunks, 1):
        parsed = _extract_meeting_metadata(chunk, default_index=idx)
        parsed_meetings.append(parsed)

    is_dry_run = (
        os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
        or os.getenv("MOCK_LLM", "").lower() in ("true", "1", "yes")
        or not os.getenv("OPENROUTER_API_KEY")
    )

    analysis_data: Dict[str, Any] = {}

    if is_dry_run:
        print("[Node: analyze_meetings] Dry-run mode: using deterministic cross-meeting analysis.")
        analysis_data = _get_deterministic_fixture_analysis(parsed_meetings)
    else:
        print(f"[Node: analyze_meetings] Calling OpenRouter ({os.getenv('OPENROUTER_MODEL', 'openrouter/free')})...")
        system_prompt = _load_system_prompt()
        
        user_content_parts = ["Here are the transcripts from the meetings this week to analyze:\n"]
        for m in parsed_meetings:
            user_content_parts.append(
                f"=== Meeting {m['index']}: {m['title']} (Date: {m['date']}) ===\n"
                f"Participants: {', '.join(m.get('participants', []))}\n"
                f"Transcript:\n{m['clean_transcript']}\n"
            )
        user_prompt = "\n".join(user_content_parts)

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)
            analysis_data = _extract_json_from_llm_response(content)
        except Exception as e:
            logger.warning(f"LLM call or JSON parsing failed ({e}). Using robust deterministic reasoning.")
            analysis_data = _get_deterministic_fixture_analysis(parsed_meetings)

    recurring_topics = (
        analysis_data.get("recurring_topics")
        or analysis_data.get("stuck_topics")
        or analysis_data.get("topics")
        or analysis_data.get("unresolved_topics")
        or []
    )
    if not recurring_topics:
        deterministic = _get_deterministic_fixture_analysis(parsed_meetings)
        recurring_topics = deterministic.get("recurring_topics", [])
        if not analysis_data.get("decision_velocity"):
            analysis_data["decision_velocity"] = deterministic.get("decision_velocity", {})
        if not analysis_data.get("commitment_load"):
            analysis_data["commitment_load"] = deterministic.get("commitment_load", {})
        if not analysis_data.get("meeting_necessity_scores"):
            analysis_data["meeting_necessity_scores"] = deterministic.get("meeting_necessity_scores", {})

    decision_velocity = analysis_data.get("decision_velocity") or {}
    commitment_load = analysis_data.get("commitment_load") or {}
    agenda_outcome_gaps = analysis_data.get("agenda_outcome_gaps") or []
    meeting_necessity_scores = analysis_data.get("meeting_necessity_scores") or {}

    overloaded_names = [p["name"] for p in commitment_load.get("overloaded_people", [])]
    stuck_topic_names = [t["topic"] for t in recurring_topics if t.get("is_stuck")]

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="analyze_meetings",
        what_it_decided="Completed cross-meeting reasoning across all transcripts",
        input_summary=f"Ingested and analyzed {len(parsed_meetings)} meeting transcript(s)",
        output_summary=(
            f"Detected {len(stuck_topic_names)} stuck topic(s) ({', '.join(stuck_topic_names) or 'None'}). "
            f"Overloaded individual(s): {', '.join(overloaded_names) or 'None'}."
        ),
        tool_calls=[],
    )

    return {
        "parsed_meetings": parsed_meetings,
        "recurring_topics": recurring_topics,
        "decision_velocity": decision_velocity,
        "commitment_load": commitment_load,
        "agenda_outcome_gaps": agenda_outcome_gaps,
        "meeting_necessity_scores": meeting_necessity_scores,
        "reasoning_trace": new_trace,
    }
