from django.db import models


class HNBatch(models.Model):
    number = models.PositiveIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"HNBatch #{self.number}"


class HNStory(models.Model):
    batch = models.ForeignKey(HNBatch, on_delete=models.CASCADE, related_name="stories")
    hn_id = models.PositiveIntegerField()
    rank = models.PositiveIntegerField()
    title = models.TextField()
    url = models.URLField()

    def __str__(self) -> str:
        return f"{self.rank}. {self.title}"


class HNStoryContent(models.Model):
    story = models.OneToOneField(HNStory, on_delete=models.CASCADE, related_name="content")
    extracted_text = models.TextField(blank=True)
    word_count = models.PositiveIntegerField(default=0)
    error = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Content for {self.story_id}"


class HNStorySummary(models.Model):
    story = models.ForeignKey(HNStory, on_delete=models.CASCADE, related_name="summaries")
    summary_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Summary for {self.story_id}"


class HNOverviewArticle(models.Model):
    batch = models.ForeignKey(HNBatch, on_delete=models.CASCADE, related_name="overviews")
    bio_hash = models.CharField(max_length=64)
    article_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("batch", "bio_hash")

    def __str__(self) -> str:
        return f"Overview for batch {self.batch_id}"


class Job(models.Model):
    class Kind(models.TextChoices):
        FETCH_BATCH = "FETCH_BATCH", "FETCH_BATCH"
        ANALYZE_BATCH = "ANALYZE_BATCH", "ANALYZE_BATCH"

    class Status(models.TextChoices):
        QUEUED = "QUEUED", "QUEUED"
        RUNNING = "RUNNING", "RUNNING"
        COMPLETE = "COMPLETE", "COMPLETE"
        ERROR = "ERROR", "ERROR"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    progress_current = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    message = models.CharField(max_length=255, blank=True)
    error = models.TextField(null=True, blank=True)
    batch = models.ForeignKey(HNBatch, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.kind} ({self.status})"
