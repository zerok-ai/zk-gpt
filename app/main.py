from flask import Flask, jsonify, request
import resource
from fastapi import FastAPI
from typing import List, Tuple, Any
from pydantic.main import BaseModel
import pineconeops

app = Flask(__name__)

pineconeOps = pineconeops.PineconeOperations()

class Data(BaseModel):
    payload: List[Tuple[Any, Any]]


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
    rca = resource.getIncidentRCA(issue_id, incident_id)
    return jsonify({"payload": {"rca": rca}})


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
        return jsonify({"payload": {"query": query , "answer": answer}})
    else:
        return jsonify({"error": "Missing 'query' parameter in the request body."}), 400    

@app.route('/v1/c/gpt/issue/observation', methods=['POST'])
def issue_observation_with_params():
    data = request.get_json()
    print(str(data))
    query = data['query']
    temperature = data['temperature']
    topK = data['topK']
    vectorEmbeddingModel = data['vectorEmbeddingModel']
    gptModel = data['gptModel']
    issue_id = data['issueId']
    answer = resource.getIssueObservationWithParams(issue_id, query,temperature,topK,vectorEmbeddingModel,gptModel)
    return jsonify({"payload": {"query": query,"issueId": issue_id,"temperature":  temperature,"vectorEmbeddingModel": vectorEmbeddingModel,"topK": topK,"gptModel": gptModel,"Answer": answer}})
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
