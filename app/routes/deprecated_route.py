import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services import inference_service, issue_service

router = APIRouter()
inference_service_impl = inference_service.InferenceService()
issue_service_impl = issue_service.IssueService()


@router.post('/v1/c/gpt/issue/inference/feedback')
def issue_inference_user_feedback(request: Request):
    data = request.json()
    request_id = data['requestId']
    feedback = data['feedback']
    score = data['score']
    inference_service_impl.update_user_issue_observation_feedback(request_id, feedback, score)
    return {"message": "Feedback received successfully"}, 200


@router.post('/v1/c/gpt/issue/observation')
def issue_observation_with_params(request: Request):
    data = request.json()
    request_id = str(uuid.uuid4())
    query = data['query']
    temperature = data['temperature']
    top_k = data['topK']
    vector_embedding_model = data['vectorEmbeddingModel']
    gpt_model = data['gptModel']
    issue_id = data['issueId']
    answer = inference_service_impl.get_issue_observation_with_params(issue_id, query, temperature, top_k, vector_embedding_model,
                                                        gpt_model, request_id)

    return {
        "payload": {
            "query": query,
            "issueId": issue_id,
            "temperature": temperature,
            "vectorEmbeddingModel": vector_embedding_model,
            "topK": top_k,
            "gptModel": gpt_model,
            "Answer": answer,
            "requestId": request_id
        }
    }


@router.post('/v1/c/gpt/issue/{issue_id}/observation')
def issue_observation(issue_id: int, request: Request):
    data = request.json()
    print(str(data))
    if 'query' in data:
        query = data['query']
        print(query)
        answer = inference_service_impl.get_issue_observation(issue_id, query)
        return JSONResponse(content={"payload": {"query": query, "answer": answer}})
    else:
        return JSONResponse(content={"error": "Missing 'query' parameter in the request body."}, status_code=400)


@router.post('/v1/c/gpt/issue/{issue_id}/incident/{incident_id}')
def query_incident(issue_id: int, incident_id: int, request: Request):
    data = request.json()
    if 'query' in data:
        query = data['query']
        answer = issue_service_impl.get_incident_query(issue_id, incident_id, query)
        return JSONResponse(content={"payload": {"answer": answer}})
    else:
        return JSONResponse(content={"error": "Missing 'query' parameter in the request body."}, status_code=400)


@router.post('/v1/c/gpt/issue/event')
def ingest_and_retrieve_incident_event_response(request: Request):
    data = request.json()
    issue_id = data['issueId']
    incident_id = data['incidentId']

    if 'event' in data:
        event_request = data['event']
        event_type = event_request['type']
        event_response = inference_service_impl.process_incident_event_and_get_event_response(issue_id, incident_id, event_type, event_request)
        return event_response
    else:
        return JSONResponse(content={"error": "Missing 'event' parameter in the request body."}, status_code=400)