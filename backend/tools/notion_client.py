"""
Notion Client Wrapper for Swytchcode / Notion API integration.

Provides typed, robust functions to:
- create_page(parent_id, title, content_blocks) -> url
- search_pages(query) -> list[dict]
- read_page(page_id) -> dict

Supports mock/dry-run mode for offline development and testing.
"""

import os
import uuid
import logging
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
import swytchcode_runtime

load_dotenv()

logger = logging.getLogger("meetloop.tools.notion")


class NotionClientError(Exception):
    """Base exception for Notion tool wrapper errors."""
    pass


class NotionAuthError(NotionClientError):
    """Raised when authentication with Notion/Swytchcode fails."""
    pass


class NotionPageNotFoundError(NotionClientError):
    """Raised when a specified Notion page cannot be found."""
    pass


def _is_dry_run(explicit_mock: bool = False) -> bool:
    if explicit_mock:
        return True
    env_dry_run = os.getenv("DRY_RUN", "").lower() in ("true", "1", "yes")
    env_mock = os.getenv("MOCK_TOOLS", "").lower() in ("true", "1", "yes")
    api_key = os.getenv("SWYTCHCODE_API_KEY") or os.getenv("NOTION_API_KEY")
    return env_dry_run or env_mock or not api_key


def create_page(
    parent_id: Optional[str] = None,
    title: str = "Untitled",
    content_blocks: Optional[Union[List[Dict[str, Any]], List[str], str]] = None,
    mock: bool = False,
) -> str:
    """
    Creates a new page in Notion under parent_id with the given title and content blocks.
    
    Returns the URL of the created Notion page.
    """
    parent_id = parent_id or os.getenv("NOTION_HEALTH_REPORT_PARENT_PAGE_ID", "mock_parent_id")
    dry_run = _is_dry_run(mock)

    if dry_run:
        fake_id = uuid.uuid4().hex[:12]
        clean_title_slug = "".join(c if c.isalnum() else "-" for c in title.lower())[:30]
        mock_url = f"https://notion.so/meetloop/{clean_title_slug}-{fake_id}"
        logger.info(f"[DRY-RUN] Notion create_page: title='{title}', parent='{parent_id}' -> {mock_url}")
        return mock_url

    # Format blocks if list of strings
    formatted_children = []
    if isinstance(content_blocks, str):
        formatted_children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content_blocks}}]
                },
            }
        ]
    elif isinstance(content_blocks, list):
        for block in content_blocks:
            if isinstance(block, str):
                formatted_children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": block}}]
                    },
                })
            elif isinstance(block, dict):
                formatted_children.append(block)

    payload = {
        "parent": {"page_id": parent_id} if parent_id else {"workspace": True},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": formatted_children[:100],  # Notion API block limit per request
    }

    try:
        res = swytchcode_runtime.exec(
            "notion.page.create",
            input={"body": payload}
        )
        data = res.get("data", {}) if isinstance(res, dict) else {}
        page_id = data.get("id") or data.get("page_id")
        page_url = data.get("url") or (f"https://www.notion.so/{page_id.replace('-', '')}" if page_id else "https://notion.so/meetloop/team-health-report")
        logger.info(f"[LIVE] Notion page created successfully -> {page_url}")
        return page_url
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg:
            raise NotionAuthError("Notion/Swytchcode authentication failed. Check your API key.") from e
        raise NotionClientError(f"Failed to create Notion page via Swytchcode: {err_msg}") from e


def search_pages(
    query: str,
    mock: bool = False,
) -> List[Dict[str, Any]]:
    """
    Searches Notion workspace for pages matching the query string.
    
    Returns a list of structured page dictionaries: [{id, title, url, snippet, last_edited_time}].
    """
    dry_run = _is_dry_run(mock)

    if dry_run:
        logger.info(f"[DRY-RUN] Notion search_pages: query='{query}'")
        q_lower = query.lower()
        if "pricing" in q_lower:
            return [
                {
                    "id": "page_pricing_01",
                    "title": "Pricing Strategy - Tier Alignment Q3",
                    "url": "https://notion.so/meetloop/pricing-strategy-q3",
                    "snippet": "Discussed 3 tiers: Free, Pro, Enterprise. Blocked on seat vs usage metric.",
                    "last_edited_time": "2026-09-24T14:30:00Z",
                },
                {
                    "id": "page_decision_pricing",
                    "title": "[Decision Page] Pricing Strategy Finalization",
                    "url": "https://notion.so/meetloop/decision-pricing-strategy",
                    "snippet": "Stuck topic from 3 standups. Suggested owner: Arjun. Action: Pick seat-based model.",
                    "last_edited_time": "2026-09-25T10:15:00Z",
                }
            ]
        elif "infra" in q_lower or "cloud" in q_lower:
            return [
                {
                    "id": "page_infra_01",
                    "title": "Infrastructure Migration to GPU Clusters",
                    "url": "https://notion.so/meetloop/infra-migration-notes",
                    "snippet": "Evaluation between AWS and GCP. Cost estimate: $12k/mo. Owner: Priya.",
                    "last_edited_time": "2026-09-22T09:00:00Z",
                }
            ]
        else:
            return [
                {
                    "id": f"page_{uuid.uuid4().hex[:8]}",
                    "title": f"Notes on {query}",
                    "url": f"https://notion.so/meetloop/notes-{query.lower().replace(' ', '-')[:20]}",
                    "snippet": f"Previous discussions and action items regarding {query}.",
                    "last_edited_time": "2026-09-23T11:00:00Z",
                }
            ]

    try:
        res = swytchcode_runtime.exec("notion.search.create", input={"body": {"query": query}})
        data = res.get("data", {}) if isinstance(res, dict) else {}
        results = []
        for item in data.get("results", []):
            title = "Untitled"
            if "properties" in item and "title" in item["properties"]:
                title_objs = item["properties"]["title"].get("title", [])
                if title_objs:
                    title = title_objs[0].get("plain_text", "Untitled")
            results.append({
                "id": item.get("id"),
                "title": title,
                "url": item.get("url", f"https://notion.so/{item.get('id')}"),
                "snippet": item.get("snippet", ""),
                "last_edited_time": item.get("last_edited_time"),
            })
        return results
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg:
            raise NotionAuthError("Notion/Swytchcode auth error during search.") from e
        raise NotionClientError(f"Failed to search Notion pages: {err_msg}") from e


def read_page(
    page_id: str,
    mock: bool = False,
) -> Dict[str, Any]:
    """
    Reads a Notion page's metadata and content blocks.
    
    Returns a structured dict with page details.
    """
    dry_run = _is_dry_run(mock)

    if dry_run:
        logger.info(f"[DRY-RUN] Notion read_page: page_id='{page_id}'")
        return {
            "id": page_id,
            "title": f"Mock Notion Page ({page_id})",
            "url": f"https://notion.so/meetloop/{page_id}",
            "content": "Key takeaways: Pricing strategy discussed across 3 meetings. Decision pending owner sign-off.",
            "blocks": [
                {"type": "heading_1", "text": "Discussion Summary"},
                {"type": "paragraph", "text": "Arjun raised concerns about enterprise seat tiers."},
                {"type": "to_do", "text": "Finalize pricing spreadsheet before Friday retro", "checked": False}
            ]
        }

    try:
        res = swytchcode_runtime.exec("notion.page.get", input={"params": {"page_id": page_id}})
        data = res.get("data", {}) if isinstance(res, dict) else {}
        title = "Untitled"
        if "properties" in data and "title" in data["properties"]:
            title_objs = data["properties"]["title"].get("title", [])
            if title_objs:
                title = title_objs[0].get("plain_text", "Untitled")
        return {
            "id": data.get("id", page_id),
            "title": title,
            "url": data.get("url", f"https://notion.so/{page_id}"),
            "content": f"Notion Page: {title}",
            "raw": data,
        }
    except Exception as e:
        err_msg = str(e)
        if "404" in err_msg:
            raise NotionPageNotFoundError(f"Notion page {page_id} not found.") from e
        if "401" in err_msg:
            raise NotionAuthError("Notion/Swytchcode auth error.") from e
        raise NotionClientError(f"Failed to read Notion page {page_id}: {err_msg}") from e
