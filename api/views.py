from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .langgraph_demo import run_demo
from .models import HNBatch, HNStorySummary, Job
from .tasks import analyze_batch_job, fetch_batch_job


@api_view(["GET"])
def hello(request):
    return Response({"message": "hello from DRF"})


@api_view(["GET"])
def run_langgraph_demo(request):
    q = request.query_params.get("q", "hi")
    return Response({"result": run_demo(q)})


def _serialize_batch(batch: HNBatch, bio_hash: str | None = None) -> dict:
    stories = (
        batch.stories.select_related("content")
        .all()
        .order_by("rank")
    )
    overview = None
    if bio_hash:
        overview = batch.overviews.filter(bio_hash=bio_hash).order_by("-created_at").first()
    else:
        overview = batch.overviews.order_by("-created_at").first()

    summaries_qs = HNStorySummary.objects.filter(story__batch=batch)
    summary_map = {summary.story_id: summary.summary_text for summary in summaries_qs}

    return {
        "batch_number": batch.number,
        "created_at": batch.created_at,
        "bio_hash": bio_hash,
        "stories": [
            {
                "id": story.id,
                "rank": story.rank,
                "title": story.title,
                "url": story.url,
                "content_error": getattr(story.content, "error", None),
            }
            for story in stories
        ],
        "summaries": [
            {
                "story_id": story.id,
                "summary_text": summary_map.get(story.id),
            }
            for story in stories
            if story.id in summary_map
        ],
        "overview": (
            {
                "bio_hash": overview.bio_hash,
                "article_text": overview.article_text,
                "created_at": overview.created_at,
            }
            if overview
            else None
        ),
    }


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_fetch_batch_job(request):
    job = Job.objects.create(kind=Job.Kind.FETCH_BATCH, status=Job.Status.QUEUED)
    fetch_batch_job(job.id)
    return Response({"job_id": job.id})


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def create_analyze_batch_job(request):
    bio_text = request.data.get("bio", "")
    if not bio_text:
        return Response({"error": "bio is required"}, status=400)

    batch_number = request.data.get("batch_number")
    if batch_number is None:
        latest = HNBatch.objects.order_by("-number").first()
        if not latest:
            return Response({"error": "no batches yet"}, status=400)
        batch_number = latest.number

    job = Job.objects.create(kind=Job.Kind.ANALYZE_BATCH, status=Job.Status.QUEUED)
    analyze_batch_job(job.id, int(batch_number), bio_text)
    return Response({"job_id": job.id})


@api_view(["GET"])
def get_job(request, job_id: int):
    job = get_object_or_404(Job, id=job_id)
    return Response(
        {
            "job_id": job.id,
            "status": job.status,
            "progress_current": job.progress_current,
            "progress_total": job.progress_total,
            "message": job.message,
            "error": job.error,
            "batch_number": job.batch.number if job.batch else None,
        }
    )


@api_view(["GET"])
def get_latest_batch(request):
    batch = HNBatch.objects.order_by("-number").first()
    if not batch:
        return Response({"error": "no batches yet"}, status=404)
    bio_hash = request.query_params.get("bio_hash")
    return Response(_serialize_batch(batch, bio_hash))


@api_view(["GET"])
def get_batch(request, number: int):
    batch = get_object_or_404(HNBatch, number=number)
    bio_hash = request.query_params.get("bio_hash")
    return Response(_serialize_batch(batch, bio_hash))
