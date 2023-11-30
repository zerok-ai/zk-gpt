from typing import Dict, Any, Union

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.services import internal_demo_service
from app.services import prometheus_service

router = APIRouter()
internal_demo_service_impl = internal_demo_service.InternalDemoService()
prometheus_service = prometheus_service.PrometheusService()


@router.post('/v1/c/gpt/generatePrometheusQueriesFromAlert')
def get_issue_prometheus_queries_from_definition(data: Dict[str, Any]):
    request_data = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_prometheus_queries = prometheus_service.get_prometheus_queries_from_alert_definition(request_data)
    return JSONResponse(
        content={"payload": {"PrometheusReport": issue_prometheus_queries}}, status_code=200)


@router.post('/v1/i/gpt/processPromAlert')
def process_prometheus_alert(data: Dict[str, Any]):
    request_data = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_prometheus_queries = prometheus_service.get_prometheus_queries_from_alert_definition(request_data)
    return JSONResponse(
        content={"payload": {"PrometheusReport": issue_prometheus_queries}}, status_code=200)



@router.post('/v1/i/gpt/alertTriggered')
def alert_triggered_inference(data: Dict[str,Union[str,Any]]):
    alert_info = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert Information is None")


