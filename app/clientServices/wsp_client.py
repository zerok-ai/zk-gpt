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


def publish_inference_to_slack(issue_id, incident_id, inference):
    url = "http://localhost:8989/request"
    payload = json.dumps({})
    headers = {
        'X-PROXY-DESTINATION': zk_slack_host,
        'X-CLIENT-ID': cluster_id,
        'Content-Type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    return
