import json
import redis
import requests
import config

axon_host = config.configuration.get("axon_host", "localhost:8080")
redis_host = config.configuration.get("redis_host", "localhost")
redis_db = config.configuration.get("redis_db", 6)
redis_pass = config.configuration.get("redis_password", "")
cluster_id = config.configuration.get("clusterId", "")
zk_slack_host = config.configuration.get("zk_slack_host", "localhost:8080")
wsp_host = config.configuration.get("wsp_host", "localhost:8080")


def publish_inference_to_slack(issue_id, incident_id, inference, issueTimeStamp):
    url = wsp_host
    payload = {
        "issueId": issue_id,
        "incidentId": incident_id,
        "inference": inference,
        "issueTimestamp": issueTimeStamp,
        "clusterId": cluster_id,
        "issueUrl": "issueUrl"
    }
    headers = {
        'X-PROXY-DESTINATION': zk_slack_host,
        'X-CLIENT-ID': cluster_id,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"An error occurred while reporting inference to slack : {e}")
        raise Exception("failed to push inference")

