from django.contrib import admin

from .models import (
    HNBatch,
    HNOverviewArticle,
    HNStory,
    HNStoryContent,
    HNStorySummary,
    Job,
)

admin.site.register(HNBatch)
admin.site.register(HNStory)
admin.site.register(HNStoryContent)
admin.site.register(HNStorySummary)
admin.site.register(HNOverviewArticle)
admin.site.register(Job)
