from flask import Flask, jsonify, request
import resource
import config
import uuid

app = Flask(__name__)


@app.route('/v1/c/gpt/scenario/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    summary = resource.getScenarioSummary(scenario_id)
    return jsonify({"payload": {"summary": summary}})


@app.route('/v1/c/gpt/issue/<issue_id>', methods=['GET'])
def get_issue(issue_id):
    summary = resource.getIssueSummary(issue_id)
    return jsonify({"payload": {"summary": summary}})


@app.route('/v1/c/gpt/issue/<issue_id>/incident/<incident_id>', methods=['GET'])
def get_incident(issue_id, incident_id):
    rcaUsingLangchianInference = bool(request.args.get('useLangchain', default=False))
    rca = resource.getIncidentRCA(issue_id, incident_id, rcaUsingLangchianInference)
    return jsonify({"payload": {"rca": rca}})


@app.route('/v1/c/gpt/incident/inference', methods=['POST'])
def get_issue_incident_inference():
    data = request.get_json()
    issue_id = data['issueId']
    incident_id = None
    if data.get('incidentId') is not None:
        incident_id = data['incidentId']
    issue_id_res, incident_id_res, inference = resource.get_incident_likely_cause(issue_id, incident_id)
    return jsonify({"payload": {"issueId": issue_id_res, "incidentId": incident_id_res, "inference": inference}})

@app.route('/v1/c/gpt/incident/{issue_id}/list/events', methods=['GET'])
def get_issue_incident_list_events():
    issue_id = data['issueId']
    if data.get('incidentId') is not None:
        incident_id = data['incidentId']
    issue_id_res, incident_id_res, inference = resource.get_incident_likely_cause(issue_id, incident_id)
    return jsonify({"payload": {"issueId": issue_id_res, "incidentId": incident_id_res, "inference": inference}})



@app.route('/v1/c/gpt/issue/<issue_id>/incident/<incident_id>', methods=['POST'])
def query_incident(issue_id, incident_id):
    data = request.get_json()
    if 'query' in data:
        query = data['query']
        answer = resource.getIncidentQuery(issue_id, incident_id, query)
        return jsonify({"payload": {"answer": answer}})
    else:
        return jsonify({"error": "Missing 'query' parameter in the request body."}), 400


@app.route('/v1/c/gpt/issue/<issue_id>/observation', methods=['POST'])
def issue_observation(issue_id):
    data = request.get_json()
    print(str(data))
    if 'query' in data:
        query = data['query']
        print(query)
        answer = resource.getIssueObservation(issue_id, query)
        return jsonify({"payload": {"query": query, "answer": answer}})
    else:
        return jsonify({"error": "Missing 'query' parameter in the request body."}), 400


@app.route('/v1/c/gpt/issue/observation', methods=['POST'])
def issue_observation_with_params():
    data = request.get_json()
    print(str(data))
    requestId = str(uuid.uuid4())
    query = data['query']
    temperature = data['temperature']
    topK = data['topK']
    vectorEmbeddingModel = data['vectorEmbeddingModel']
    gptModel = data['gptModel']
    issue_id = data['issueId']
    answer = resource.getIssueObservationWithParams(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel,
                                                    requestId)
    return jsonify({"payload": {"query": query, "issueId": issue_id, "temperature": temperature,
                                "vectorEmbeddingModel": vectorEmbeddingModel, "topK": topK, "gptModel": gptModel,
                                "Answer": answer, "requestId": requestId}})


@app.route('/v1/c/gpt/issue/inference/feeback', methods=['POST'])
def issue_inference_user_feedback():
    data = request.get_json()
    print(str(data))
    requestId = data['requestId']
    feedback = data['feedback']
    score = data['score']
    resource.updateUserIssueObservationFeedback(requestId, feedback, score)
    return '', 200


@app.route('/v1/c/gpt/issue/<issue_id>/getAllinferences', methods=['GET'])
def get_all_issue_inferences(issue_id):
    limit = int(request.args.get('limit', default=10))
    offset = int(request.args.get('offset', default=0))
    allUserInferences = resource.getAllIssueInferences(issue_id, limit, offset)
    return jsonify({"payload": {"issueId": issue_id, "UserInferences": allUserInferences}})


# Load config and Fetch the secrets from the server
def fetch_secrets_and_load_config():
    try:
        config.configuration
        # If successful, return True
        return True
    except Exception as e:
        print(f"Error fetching config and secrets: {str(e)}")
        return False


if __name__ == '__main__':
    if fetch_secrets_and_load_config():
        # Start the application only if the config and secrets are fetched successfully
        app.run(host='0.0.0.0', port=80)
