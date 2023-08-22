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



@app.route('/v1/health', methods=['GET'])
async def root():
    return {"message": "OK"}


@app.route('/v1/index', methods=['POST'])
async def create_index(name: str):
    return pineconeOps.create_index(index_name=name)


@app.get("/api/v1/index/stats")
async def stats():
    return pineconeOps.fetch_stats()


@app.route('/v1/connect', methods=['GET'])
async def create_index():
    return pineconeOps.connect_index()


@app.route('/api/v1/vectors',method=['POST'])
async def create_index(data: Data):
    return pineconeOps.upsert(data=data.payload)


@app.route('/v1/search-vector',method=['POST'])
async def create_index(payload: List[Any]):
    return pineconeOps.query(query_vector=payload)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
