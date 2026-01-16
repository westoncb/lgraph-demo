from rest_framework.decorators import api_view
from rest_framework.response import Response

from .langgraph_demo import run_demo


@api_view(["GET"])
def hello(request):
    return Response({"message": "hello from DRF"})


@api_view(["GET"])
def run_langgraph_demo(request):
    q = request.query_params.get("q", "hi")
    return Response({"result": run_demo(q)})
