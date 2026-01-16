from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HNBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveIntegerField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="HNStory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hn_id", models.PositiveIntegerField()),
                ("rank", models.PositiveIntegerField()),
                ("title", models.TextField()),
                ("url", models.URLField()),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stories",
                        to="api.hnbatch",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HNStoryContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("extracted_text", models.TextField(blank=True)),
                ("word_count", models.PositiveIntegerField(default=0)),
                ("error", models.TextField(blank=True, null=True)),
                (
                    "story",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content",
                        to="api.hnstory",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HNStorySummary",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bio_hash", models.CharField(max_length=64)),
                ("summary_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "story",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="summaries",
                        to="api.hnstory",
                    ),
                ),
            ],
            options={
                "unique_together": {("story", "bio_hash")},
            },
        ),
        migrations.CreateModel(
            name="HNOverviewArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bio_hash", models.CharField(max_length=64)),
                ("article_text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "batch",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="overview",
                        to="api.hnbatch",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("FETCH_BATCH", "FETCH_BATCH"), ("ANALYZE_BATCH", "ANALYZE_BATCH")], max_length=20)),
                ("status", models.CharField(choices=[("QUEUED", "QUEUED"), ("RUNNING", "RUNNING"), ("COMPLETE", "COMPLETE"), ("ERROR", "ERROR")], default="QUEUED", max_length=20)),
                ("progress_current", models.PositiveIntegerField(default=0)),
                ("progress_total", models.PositiveIntegerField(default=0)),
                ("message", models.CharField(blank=True, max_length=255)),
                ("error", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "batch",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="api.hnbatch",
                    ),
                ),
            ],
        ),
    ]
