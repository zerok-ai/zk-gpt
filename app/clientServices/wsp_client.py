import json
import requests
import config

axon_host = config.configuration.get("axon_host", "localhost:8080")
redis_host = config.configuration.get("redis_host", "localhost")
redis_db = config.configuration.get("redis_db", 6)
redis_pass = config.configuration.get("redis_password", "")
cluster_id = config.configuration.get("clusterId", "")
zk_slack_host = config.configuration.get("zk_slack_host", "localhost:8080")
wsp_host = config.configuration.get("wsp_host", "localhost:8080")


def publish_inference_to_slack(issue_id, incident_id, inference, issue_title):
    url = wsp_host
    payload = {
        "issueId": issue_id,
        "incidentId": incident_id,
        "issueTitle": issue_title,
        "inference": inference,
        "clusterId": cluster_id
    }
    headers = {
        'X-PROXY-DESTINATION': zk_slack_host,
        'X-CLIENT-ID': cluster_id,
        'Content-Type': 'application/json'
    }
    try:
        # Convert the payload to JSON
        payload_json = json.dumps(payload)
        print(f"pushing inference data to slack for issueId : {issue_id}")
        # Make a POST request
        response = requests.post(url, headers=headers, data=payload_json)
        response.raise_for_status()
    except Exception as e:
        print(f"An error occurred while reporting inference to slack : {e}")
        raise Exception("failed to push inference")

