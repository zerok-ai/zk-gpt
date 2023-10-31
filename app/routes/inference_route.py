from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.services import issue_service, inference_service

router = APIRouter()
issue_service = issue_service.IssueService()
inference_service = inference_service.InferenceService()


@router.get('/v1/c/gpt/scenario/{scenario_id}')
async def get_scenario(scenario_id: str):
    summary = issue_service.get_scenario_summary(scenario_id)
    return {"payload": {"summary": summary}}


@router.get('/v1/c/gpt/issue/{issue_id}')
async def get_issue(issue_id: str):
    summary = issue_service.get_issue_summary(issue_id)
    return JSONResponse(content={"payload": {"summary": summary}})


@router.get('/v1/c/gpt/issue/{issue_id}/getAllinferences')
def get_all_issue_inferences(issue_id: int,
                             limit: int = Query(default=10, description="Number of items to return", ge=1),
                             offset: int = Query(default=0, description="Offset for pagination", ge=0)):
    all_user_inferences = inference_service.get_all_issue_inferences(issue_id, limit, offset)
    return {"payload": {"issueId": issue_id, "UserInferences": all_user_inferences}}


@router.post('/v1/c/gpt/incident/inference')
def get_issue_incident_inference(request: Request):
    data = request.json()
    issue_id = data['issueId']
    incident_id = data['incidentId']
    issue_id_res, incident_id_res, inference = inference_service.get_incident_likely_cause(issue_id, incident_id)
    return JSONResponse(content={
        "payload": {
            "issueId": issue_id_res,
            "incidentId": incident_id_res,
            "inference": inference
        }
    })


@router.get('/v1/c/gpt/issue/{issue_id}/incident/{incident_id}')
def get_incident(issue_id: int, incident_id: int,
                 use_langchain: bool = Query(default=False, description="Use Langchain Inference")):
    rca = issue_service.get_incident_rca(issue_id, incident_id, use_langchain)
    return JSONResponse(content={"payload": {"rca": rca}})
