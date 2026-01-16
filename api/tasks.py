from __future__ import annotations

import hashlib

from django.db import transaction
from huey.contrib.djhuey import task

from api.models import (
    HNBatch,
    HNOverviewArticle,
    HNStory,
    HNStoryContent,
    HNStorySummary,
    Job,
)
from api.services.analysis_graph import run_overview_generation, run_summary_analysis
from api.services.extract import extract_article_text
from api.services.hn import get_item, get_top_story_ids


def _next_batch_number() -> int:
    last = HNBatch.objects.order_by("-number").first()
    return 1 if not last else last.number + 1


def _update_job(job: Job, **kwargs) -> None:
    for key, value in kwargs.items():
        setattr(job, key, value)
    update_fields = list(kwargs.keys())
    if "updated_at" not in update_fields:
        update_fields.append("updated_at")
    job.save(update_fields=update_fields)


@task()
def fetch_batch_job(job_id: int) -> None:
    job = Job.objects.get(id=job_id)
    _update_job(job, status=Job.Status.RUNNING, message="Fetching top stories")

    try:
        with transaction.atomic():
            batch = HNBatch.objects.create(number=_next_batch_number())
            job.batch = batch
            job.progress_total = 0
            job.progress_current = 0
            job.message = "Created batch"
            job.save()

        story_ids = get_top_story_ids()
        picked: list[dict] = []
        for item_id in story_ids:
            item = get_item(item_id)
            if item["url"]:
                picked.append(item)
            if len(picked) == 10:
                break

        if not picked:
            raise RuntimeError("No top stories with URLs available.")

        _update_job(job, progress_total=len(picked), progress_current=0, message="Fetched story list")

        for idx, item in enumerate(picked, start=1):
            story = HNStory.objects.create(
                batch=batch,
                hn_id=item["id"],
                rank=idx,
                title=item["title"],
                url=item["url"],
            )
            text, word_count, error = extract_article_text(item["url"])
            HNStoryContent.objects.create(
                story=story,
                extracted_text=text,
                word_count=word_count,
                error=error,
            )
            _update_job(job, progress_current=idx, message=f"Fetched {idx}/{len(picked)}")

        _update_job(job, status=Job.Status.COMPLETE, message="Batch fetched")
    except Exception as exc:
        _update_job(
            job,
            status=Job.Status.ERROR,
            error=str(exc),
            message="Failed to fetch batch",
        )


@task()
def analyze_batch_job(job_id: int, batch_number: int, bio_text: str) -> None:
    job = Job.objects.get(id=job_id)
    _update_job(job, status=Job.Status.RUNNING, message="Analyzing batch")

    try:
        batch = HNBatch.objects.get(number=batch_number)
        _update_job(job, batch=batch)
        bio_hash = hashlib.sha256(bio_text.encode("utf-8")).hexdigest()
        story_ids = list(batch.stories.order_by("rank").values_list("id", flat=True))
        existing_count = HNStorySummary.objects.filter(story_id__in=story_ids).count()

        summaries: list[dict] = []
        if existing_count < len(story_ids):
            _update_job(job, message="Generating summaries")
            result = run_summary_analysis(batch_number=batch_number)
            summaries = result.get("summaries", [])
            _update_job(job, progress_total=len(summaries) + 1, progress_current=0)

            for idx, summary in enumerate(summaries, start=1):
                HNStorySummary.objects.update_or_create(
                    story_id=summary["story_id"],
                    defaults={"summary_text": summary["summary"]},
                )
                _update_job(job, progress_current=idx, message=f"Saved summary {idx}/{len(summaries)}")
        else:
            _update_job(job, progress_total=len(story_ids) + 1, progress_current=0, message="Summaries already exist")
            summaries = [
                {
                    "story_id": story.id,
                    "title": story.title,
                    "url": story.url,
                    "summary": HNStorySummary.objects.filter(story=story)
                    .order_by("-created_at")
                    .values_list("summary_text", flat=True)
                    .first(),
                }
                for story in batch.stories.order_by("rank")
            ]

        overview_text = run_overview_generation(bio_text=bio_text, summaries=summaries)
        HNOverviewArticle.objects.update_or_create(
            batch=batch,
            bio_hash=bio_hash,
            defaults={"article_text": overview_text},
        )

        _update_job(job, progress_current=len(summaries) + 1, message="Saved overview")
        _update_job(job, status=Job.Status.COMPLETE, message="Analysis complete")
    except Exception as exc:
        _update_job(
            job,
            status=Job.Status.ERROR,
            error=str(exc),
            message="Failed to analyze batch",
        )
