from fastapi import HTTPException, Path, Body, APIRouter, Query
from fastapi.responses import JSONResponse

from app.services import user_events_service, issue_service

router = APIRouter()
issue_service_impl = issue_service.IssueService()
user_events_service_impl = user_events_service.UserEventsService()


@router.post('/v1/c/gpt/issue/{issue_id}/incident/{incident_id}')
async def query_incident(
        issue_id: str = Path(..., description="Issue ID"),
        incident_id: str = Path(..., description="Incident ID"),
        data: dict = Body(..., description="Request body containing 'query' parameter")
):
    if 'query' in data:
        query = data['query']
        answer = issue_service_impl.get_incident_query(issue_id, incident_id, query)
        return {"payload": {"answer": answer}}
    else:
        raise HTTPException(status_code=400, detail="Missing 'query' parameter in the request body")


@router.get('/v1/c/gpt/incident/{issue_id}/list/events')
def get_issue_incident_list_events(issue_id: int,
                                   limit: int = Query(default=10, description="Number of items to return", ge=1),
                                   offset: int = Query(default=0, description="Offset for pagination", ge=0)):
    total_count, user_conserve_events_response = user_events_service_impl.get_user_conversation_events(issue_id, limit, offset)

    return JSONResponse(content={
        "payload": {
            "issueId": issue_id,
            "events": user_conserve_events_response,
            "total_count": total_count
        }
    })


