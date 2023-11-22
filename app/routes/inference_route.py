from typing import Dict, Any

from fastapi import APIRouter, Query, Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.response.generic_response import GenericResponse
from app.services import issue_service, inference_service, prometheus_service
from app.models.request.fetch_inference_request import FetchInferenceRequest
from app.models.response.fetch_inference_respone import FetchInferenceResponse, FetchInferenceResponseDashboard

router = APIRouter()
issue_service = issue_service.IssueService()
inference_service = inference_service.InferenceService()
prometheus_service = prometheus_service.PrometheusService()


@router.get('/v1/c/gpt/scenario/{scenario_id}')
async def get_scenario(scenario_id: str):
    summary = issue_service.get_scenario_summary(scenario_id)
    return {"payload": {"summary": summary}}


@router.get('/v1/c/gpt/issue/{issue_id}')
async def get_issue(issue_id: str):
    summary = issue_service.get_issue_summary(issue_id)
    return JSONResponse(content={"payload": {"summary": summary}})


@router.get('/v1/c/gpt/issue/{issue_id}/getAllinferences')
def get_all_issue_inferences(issue_id: str,
                             limit: int = Query(default=10, description="Number of items to return", ge=1),
                             offset: int = Query(default=0, description="Offset for pagination", ge=0)):
    all_user_inferences = inference_service.get_all_issue_inferences(issue_id, limit, offset)
    return {"payload": {"issueId": issue_id, "UserInferences": all_user_inferences}}


@router.post('/v1/c/gpt/incident/inference')
def get_issue_incident_inference(data: Dict[str, Any]):
    request_data = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_id = request_data.get('issueId')
    incident_id = request_data.get('incidentId')
    fetch_inference_response = inference_service.get_incident_likely_cause(issue_id, incident_id)
    response = FetchInferenceResponseDashboard(payload=fetch_inference_response)
    return JSONResponse(content=response.to_dict(), status_code=200)



@router.get('/v1/c/gpt/issue/{issue_id}/incident/{incident_id}', response_model=GenericResponse)
def get_incident_rca(issue_id: str, incident_id: str,
                 use_langchain: bool = Query(default=False, description="Use Langchain Inference")):
    rca = issue_service.get_incident_rca(issue_id, incident_id, use_langchain)
    return GenericResponse(payload=rca)


@router.post('/v1/c/gpt/generatePrometheusReport')
def get_issue_prometheus_report(data: Dict[str, Any]):
    request_data = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_id = request_data.get('issueId')
    incident_id = request_data.get('incidentId')
    issue_prometheus_report = prometheus_service.get_prometheus_report(issue_id, incident_id)
    return JSONResponse(
        content={"payload": {"issueId": issue_id, "incidentId": incident_id, "PrometheusReport": issue_prometheus_report}}, status_code=200)


@router.post('/v1/c/gpt/generatePrometheusQueriesFromAlert')
def get_issue_prometheus_queries_from_definition(data: Dict[str, Any]):
    request_data = data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_prometheus_queries = prometheus_service.get_prometheus_queries_from_alert_definition(request_data)
    return JSONResponse(
        content={"payload": {"PrometheusReport": issue_prometheus_queries}}, status_code=200)
