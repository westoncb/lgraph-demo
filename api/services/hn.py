from __future__ import annotations

import httpx

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"


def get_top_story_ids() -> list[int]:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{HN_BASE_URL}/topstories.json")
        resp.raise_for_status()
        data = resp.json()
    return [int(item) for item in data]


def get_item(item_id: int) -> dict:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{HN_BASE_URL}/item/{item_id}.json")
        resp.raise_for_status()
        data = resp.json()
    return {
        "id": data.get("id", item_id),
        "title": data.get("title", ""),
        "url": data.get("url") or "",
    }
