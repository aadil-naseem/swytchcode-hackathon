"""
Phase 8 & 14 - Audit Mode: Pattern Extraction Node.
"""

import re
from typing import Any, Dict, List
from backend.agent.state import ClearRoomState
from backend.observability import append_trace_step


def _find_evidence_for_topic(topic_name: str, parsed_meetings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    evidence = []
    keywords = [w.lower() for w in re.findall(r"\w+", topic_name) if len(w) > 3]
    if not keywords:
        keywords = [topic_name.lower()]

    for m in parsed_meetings:
        text = m.get("clean_transcript", "")
        text_lower = text.lower()
        if any(kw in text_lower for kw in keywords):
            sentences = re.split(r"[.\n]+", text)
            matching_lines = [s.strip() for s in sentences if any(kw in s.lower() for kw in keywords)]
            snippet = " ... ".join(matching_lines[:2]) if matching_lines else text[:150]
            evidence.append({
                "meeting_title": m.get("title", f"Meeting {m.get('index', 1)}"),
                "date": m.get("date", ""),
                "snippet": snippet[:250],
            })
    return evidence


def extract_patterns_node(state: ClearRoomState) -> Dict[str, Any]:
    print("[Node: extract_patterns] Ranking stuck topics, commitment loads, and meeting efficiency...")

    parsed_meetings = state.get("parsed_meetings") or []
    recurring_topics = state.get("recurring_topics") or []
    decision_velocity = state.get("decision_velocity") or {}
    commitment_load = state.get("commitment_load") or {}
    agenda_outcome_gaps = state.get("agenda_outcome_gaps") or []

    stuck_candidates = []
    for t in recurring_topics:
        is_stuck = (
            t.get("is_stuck", False)
            or str(t.get("status", "")).lower() in ("unresolved", "stuck", "pending", "open", "in_progress")
            or t.get("meeting_count", 0) >= 1
            or bool(t.get("blocking_reason"))
        )
        if is_stuck:
            topic_name = t.get("topic", "Unresolved Topic")
            evidence = _find_evidence_for_topic(topic_name, parsed_meetings)
            stuck_candidates.append({
                "topic": topic_name,
                "meeting_count": t.get("meeting_count", len(evidence) or 1),
                "meeting_titles": t.get("meeting_titles", [e["meeting_title"] for e in evidence]),
                "dates": t.get("dates", [e["date"] for e in evidence]),
                "summary_of_discussion": t.get("summary_of_discussion", ""),
                "blocking_reason": t.get("blocking_reason", ""),
                "suggested_owner": t.get("suggested_owner", ""),
                "suggested_next_step": t.get("suggested_next_step", ""),
                "evidence": evidence,
            })

    stuck_candidates.sort(key=lambda x: x.get("meeting_count", 0), reverse=True)
    # Swytchcode Policy Guardrail: Cap decision page generation to top 5 high-impact stuck topics per run
    stuck_candidates = stuck_candidates[:5]

    counts = commitment_load.get("counts_by_person", {})
    total_action_items = sum(counts.values()) or 1
    ranked_team = []
    overloaded_people = []

    for person, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        share_pct = round((count / total_action_items) * 100, 1)
        is_overloaded = share_pct >= 40.0 or count >= 5
        entry = {
            "name": person,
            "action_item_count": count,
            "percentage_of_all_tasks": share_pct,
            "is_overloaded": is_overloaded,
        }
        ranked_team.append(entry)
        if is_overloaded:
            existing_overloaded = next(
                (p for p in commitment_load.get("overloaded_people", []) if p.get("name") == person),
                {}
            )
            entry["assessment"] = existing_overloaded.get(
                "assessment",
                f"Critical bottleneck: holds {share_pct}% of all team tasks."
            )
            entry["action_items"] = existing_overloaded.get("action_items", [])
            overloaded_people.append(entry)

    refined_commitment_load = {
        "counts_by_person": counts,
        "total_action_items": total_action_items,
        "ranked_team": ranked_team,
        "overloaded_people": overloaded_people,
        "balanced_people": [p["name"] for p in ranked_team if not p["is_overloaded"]],
    }

    meeting_type_stats: Dict[str, Dict[str, Any]] = {}
    for gap in agenda_outcome_gaps:
        title = gap.get("meeting_title", "General Sync")
        opened = gap.get("topics_opened", 1)
        resolved = gap.get("topics_resolved", 0)
        
        cat = "General Sync"
        title_lower = title.lower()
        if "standup" in title_lower:
            cat = "Daily Standup"
        elif "retro" in title_lower:
            cat = "Sprint Retrospective"
        elif "exec" in title_lower or "alignment" in title_lower:
            cat = "Executive Alignment"
        elif "product" in title_lower or "strategy" in title_lower:
            cat = "Product Strategy"

        if cat not in meeting_type_stats:
            meeting_type_stats[cat] = {"opened": 0, "resolved": 0, "count": 0}
        meeting_type_stats[cat]["opened"] += opened
        meeting_type_stats[cat]["resolved"] += resolved
        meeting_type_stats[cat]["count"] += 1

    ranked_meeting_types = []
    for cat, stats in meeting_type_stats.items():
        opened = stats["opened"] or 1
        rate = round(stats["resolved"] / opened, 2)
        ranked_meeting_types.append({
            "category": cat,
            "meetings_held": stats["count"],
            "topics_opened": stats["opened"],
            "topics_resolved": stats["resolved"],
            "resolution_rate": rate,
            "async_recommendation": "Convert to Async" if rate == 0.0 else ("Keep as Live Sync" if rate >= 0.75 else "Improve Agenda Structure"),
        })

    lowest_eff_str = "None"
    if ranked_meeting_types:
        lowest_eff_str = f"{ranked_meeting_types[0]['category']} ({int(ranked_meeting_types[0]['resolution_rate']*100)}% resolution)"

    new_trace = append_trace_step(
        existing_trace=state.get("reasoning_trace"),
        node_name="extract_patterns",
        what_it_decided="Extracted ranked stuck topics, workload distribution, and meeting resolution rates",
        input_summary=f"Processed {len(recurring_topics)} recurring topics and {len(counts)} team members",
        output_summary=(
            f"Found {len(stuck_candidates)} stuck topic candidate(s). "
            f"Top overloaded: {', '.join(p['name'] for p in overloaded_people) or 'None'}. "
            f"Lowest efficiency meeting: {lowest_eff_str}."
        ),
        tool_calls=[],
    )

    return {
        "recurring_topics": stuck_candidates,
        "commitment_load": refined_commitment_load,
        "meeting_necessity_scores": {
            **state.get("meeting_necessity_scores", {}),
            "ranked_categories": ranked_meeting_types,
        },
        "reasoning_trace": new_trace,
    }
