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
            "You summarize news articles. Write 4-6 sentences, highlight why it matters, and avoid hype."
        )
    )
    human = HumanMessage(
        content=(
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
        _summarize_story(sem, summary_model, payload)
        for payload in state["stories"]
    ]
    summaries = await asyncio.gather(*tasks)
    return {"summaries": summaries}


def run_summary_analysis(batch_number: int) -> dict[str, Any]:
    stories = _load_stories(batch_number)

    def inject_stories(state: AnalysisInput) -> dict:
        return {"stories": stories}

    builder = StateGraph(AnalysisState, input_schema=AnalysisInput)
    builder.add_node("inject_stories", inject_stories)
    builder.add_node("summarize_all", _summarize_all)
    builder.add_edge(START, "inject_stories")
    builder.add_edge("inject_stories", "summarize_all")
    builder.add_edge("summarize_all", END)

    graph = builder.compile()
    result = asyncio.run(graph.ainvoke({"batch_number": batch_number}))
    return {
        "summaries": result.get("summaries", []),
    }


def run_overview_generation(bio_text: str, summaries: list[dict]) -> str:
    _, overview_model = _get_models()
    normalized = [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "summary": item.get("summary") or "No summary available.",
        }
        for item in summaries
    ]
    bullets = "\n".join(
        f"- {item['title']} ({item['url']}): {item['summary']}"
        for item in normalized
    )
    system = SystemMessage(
        content=(
            "You write an enjoyable, informative article that incorporates key information from the summaries relevant to the user."
            "Aim for ~4 - 5 paragraphs; aim for smooth natural reading, don't be afraid to extrapolate and share insights you see that might be relevant to the specific reader whose bio info you have; don't create separate section headings or anything like that, just write a nice literate essay with a handful of paragraphs; token limit is ~3000."
        )
    )
    human = HumanMessage(
        content=(
            f"Reader bio:\n{bio_text}\n\n"
            f"Story summaries:\n{bullets}\n\n"
            "Write the article:"
        )
    )
    response = overview_model.invoke([system, human])
    return response.content.strip()
