from __future__ import annotations

import asyncio
import os
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from api.models import HNBatch


class AnalysisInput(TypedDict):
    batch_number: int
    bio_text: str


class StoryPayload(TypedDict):
    id: int
    title: str
    url: str
    text: str
    error: str | None


class AnalysisState(AnalysisInput):
    stories: list[StoryPayload]
    summaries: list[dict]
    overview_text: str


def _get_models() -> tuple[ChatOpenAI, ChatOpenAI]:
    model_name = os.environ.get("OPENAI_MODEL", "gpt-5.2")
    summary_model = ChatOpenAI(model=model_name, temperature=0.3, max_tokens=400)
    overview_tokens = int(os.environ.get("OVERVIEW_MAX_TOKENS", "3000"))
    overview_model = ChatOpenAI(model=model_name, temperature=0.4, max_tokens=overview_tokens)
    return summary_model, overview_model


def _load_stories(batch_number: int) -> list[StoryPayload]:
    batch = HNBatch.objects.prefetch_related("stories__content").get(number=batch_number)
    stories: list[StoryPayload] = []
    for story in batch.stories.all().order_by("rank"):
        content = getattr(story, "content", None)
        stories.append(
            {
                "id": story.id,
                "title": story.title,
                "url": story.url,
                "text": content.extracted_text if content else "",
                "error": content.error if content else "missing content",
            }
        )
    return stories


async def _summarize_story(
    sem: asyncio.Semaphore,
    model: ChatOpenAI,
    bio_text: str,
    payload: StoryPayload,
) -> dict:
    if payload["error"] or not payload["text"]:
        return {
            "story_id": payload["id"],
            "title": payload["title"],
            "url": payload["url"],
            "summary": "No summary available (content missing or extraction failed).",
        }

    system = SystemMessage(
        content=(
            "You summarize news articles for a reader using their bio context. "
            "Write 4-6 sentences, highlight why it matters, and avoid hype."
        )
    )
    human = HumanMessage(
        content=(
            f"Reader bio:\n{bio_text}\n\n"
            f"Title: {payload['title']}\n"
            f"URL: {payload['url']}\n\n"
            f"Article text:\n{payload['text']}\n\n"
            "Summary:"
        )
    )
    async with sem:
        response = await model.ainvoke([system, human])
    return {
        "story_id": payload["id"],
        "title": payload["title"],
        "url": payload["url"],
        "summary": response.content.strip(),
    }


async def _summarize_all(state: AnalysisState) -> dict:
    summary_model, _ = _get_models()
    concurrency = int(os.environ.get("SUMMARY_CONCURRENCY", "5"))
    sem = asyncio.Semaphore(concurrency)
    tasks = [
        _summarize_story(sem, summary_model, state["bio_text"], payload)
        for payload in state["stories"]
    ]
    summaries = await asyncio.gather(*tasks)
    return {"summaries": summaries}


async def _write_overview(state: AnalysisState) -> dict:
    _, overview_model = _get_models()
    bullets = "\n".join(
        f"- {item['title']} ({item['url']}): {item['summary']}"
        for item in state["summaries"]
    )
    system = SystemMessage(
        content=(
            "You write a concise overview article for a reader based on summaries. "
            "Aim for 6-10 paragraphs, use clear headings, and keep it under ~3000 tokens."
        )
    )
    human = HumanMessage(
        content=(
            f"Reader bio:\n{state['bio_text']}\n\n"
            f"Story summaries:\n{bullets}\n\n"
            "Write the overview article:"
        )
    )
    response = await overview_model.ainvoke([system, human])
    return {"overview_text": response.content.strip()}


def run_analysis(batch_number: int, bio_text: str) -> dict[str, Any]:
    stories = _load_stories(batch_number)

    def inject_stories(state: AnalysisInput) -> dict:
        return {"stories": stories}

    builder = StateGraph(AnalysisState, input_schema=AnalysisInput)
    builder.add_node("inject_stories", inject_stories)
    builder.add_node("summarize_all", _summarize_all)
    builder.add_node("write_overview", _write_overview)
    builder.add_edge(START, "inject_stories")
    builder.add_edge("inject_stories", "summarize_all")
    builder.add_edge("summarize_all", "write_overview")
    builder.add_edge("write_overview", END)

    graph = builder.compile()
    result = asyncio.run(graph.ainvoke({"batch_number": batch_number, "bio_text": bio_text}))
    return {
        "summaries": result.get("summaries", []),
        "overview_text": result.get("overview_text", ""),
    }
