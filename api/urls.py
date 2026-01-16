from django.urls import path
from . import views

urlpatterns = [
    path("hello/", views.hello),
    path("run-demo/", views.run_langgraph_demo),
]
