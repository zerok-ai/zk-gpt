from fastapi import HTTPException, APIRouter, Query, status
from fastapi.responses import JSONResponse

from app.models.request.gereric_request import GenericRequest
from app.models.request.user_qna_event_request import UserQnaEventRequest
from app.services import user_events_service, issue_service, inference_service

router = APIRouter()
issue_service_impl = issue_service.IssueService()
user_events_service_impl = user_events_service.UserEventsService()
inference_service_impl = inference_service.InferenceService()


@router.post('/v1/c/gpt/issue/{issue_id}/incident/{incident_id}')
def query_incident(
        issue_id: str,
        incident_id: str,
        request: GenericRequest
):
    data = request.data
    if data is None or not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    if 'query' in data:
        query = data['query']
        answer = issue_service_impl.get_incident_query(issue_id, incident_id, query)
        return {"payload": {"answer": answer}}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'query' parameter in the request body")


@router.get('/v1/c/gpt/incident/{issue_id}/list/events')
def get_issue_incident_list_events(issue_id: str,
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

@router.post('/v1/c/gpt/issue/event')
def ingest_and_retrieve_incident_event_response(request: UserQnaEventRequest):
    if request is None or not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided")
    issue_id = request.issueId
    incident_id = request.incidentId

    if request.event is not None:
        event_request = request.event
        event_type = event_request.type
        event_response = inference_service_impl.process_incident_event_and_get_event_response(issue_id, incident_id, event_type, event_request)
        return event_response
    else:
        return JSONResponse(content={"error": "Missing 'event' parameter in the request body."}, status_code=status.HTTP_400_BAD_REQUEST)


