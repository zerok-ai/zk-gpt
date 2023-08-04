from flask import Flask, jsonify, request
import resource

app = Flask(__name__)


@app.route('/v1/c/gpt/scenario/<scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    summary = resource.getScenario(scenario_id)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
