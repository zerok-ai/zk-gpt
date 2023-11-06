from typing import Dict

from fastapi import status

from app import config
from app.clients.api_client import APIClient
from app.exceptions.exception import ClientInteractionException
from app.utils import zk_logger

cluster_id = config.configuration.get("clusterId", "")
zk_slack_host = config.configuration.get("zk_slack_host", "localhost:8080")
wsp_host = config.configuration.get("wsp_host", "localhost:8080")
log_tag = "wsp_service_client"
logger = zk_logger.logger


# http://zk-wsp-client.zk-client.svc.cluster.local/request
# wsp_host : http://zk-wsp-client.zk-client.svc.cluster.local
# endpoint : request
class WSPServiceClient:
    def __init__(self):
        self.api_client = APIClient(base_url=wsp_host)

    def publish_inference_to_slack(self, issue_id: str, incident_id: str, inference: str, issue_title: str, scenario_id: str):
        endpoint = f"request"
        payload = {
            "issueId": issue_id,
            "incidentId": incident_id,
            "issueTitle": issue_title,
            "inference": inference,
            "clusterId": cluster_id,
            "scenarioId": scenario_id
        }
        headers = {
            'X-PROXY-DESTINATION': zk_slack_host,
            'X-CLIENT-ID': cluster_id,
            'Content-Type': 'application/json'
        }
        try:
            self.api_client.post_without_response(endpoint=endpoint, data=payload, headers=headers)
            logger.info(log_tag, f"inference pushed to slack for issueId : {issue_id}")
        except Exception as e:
            logger.error(log_tag, f"An error occurred while reporting inference to slack for issue: {issue_id} with "
                                  f"error: {e}")
            raise ClientInteractionException("Error occurred while pushing inference to WSP",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             f"Error occurred during API call: {e}")
