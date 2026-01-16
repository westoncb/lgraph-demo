from django.urls import path
from . import views

urlpatterns = [
    path("hello/", views.hello),
    path("run-demo/", views.run_langgraph_demo),
    path("jobs/fetch-batch/", views.create_fetch_batch_job),
    path("jobs/analyze/", views.create_analyze_batch_job),
    path("jobs/<int:job_id>/", views.get_job),
    path("batches/latest/", views.get_latest_batch),
    path("batches/<int:number>/", views.get_batch),
]
