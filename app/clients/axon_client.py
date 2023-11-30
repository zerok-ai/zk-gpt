from typing import Dict

import requests
from fastapi import status, HTTPException

from app import config
from app.clients.api_client import APIClient
from app.exceptions.exception import ClientInteractionException
from app.models.request.prom_custom_metric_data_request import PromCustomMetricDataRequest
from app.utils import zk_logger

axon_host = config.configuration.get("axon_host", "localhost:8080")
log_tag = "axon_service_client"
logger = zk_logger.logger


class AxonServiceClient:
    def __init__(self):
        self.api_client = APIClient(base_url=axon_host)

    def get_latest_issues_data(self):
        endpoint = f"v1/c/axon/issue"
        params = {"limit": 50, "offset": 0, "st": "-1500m"}
        try:
            response = self.api_client.get(endpoint=endpoint, params=params)
            data = response
            issues_data = data['payload']['issues']
            return issues_data
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error while fetching latest issue for a given time : {e}")
            raise ClientInteractionException("Error while fetching latest issue for a given time",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             str(e))

    def get_span_raw_data(self, issue_id: str, incident_id: str, span_id: str):
        endpoint = f"v1/c/axon/issue/{issue_id}/incident/{incident_id}/span/{span_id}"
        try:
            response = self.api_client.get(endpoint=endpoint)
            data = response
            span_rawdata = data['payload']['span_raw_data_details'].get(span_id)
            return span_rawdata
        except HTTPException as e:
            logger.info(log_tag, f"Error occurred while fetch span raw data ERROR: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.info(log_tag, f"Error occurred while fetch span raw data ERROR: {e}")
            return None
            # raise ClientInteractionException("error occurred while fetch span raw data", status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error occurred during API call: {e}")

    def get_issue_incidents(self, issue_id: str):
        endpoint = f"v1/c/axon/issue/{issue_id}/incident"
        params = {"limit": 50, "offset": 0}
        try:
            response = self.api_client.get(endpoint=endpoint, params=params)
            data = response
            incidents = data['payload']['trace_id_list']
            return incidents
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error while fetching incident Ids for a given issue : {e}")
            raise ClientInteractionException("Error while fetching incident Ids for a given issue",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             f"Error occurred during API call: {e}")

    def get_spans_map(self, issue_id: str, incident_id: str):
        endpoint = f"v1/c/axon/issue/{issue_id}/incident/{incident_id}"
        params = {"limit": 10, "offset": 0}
        try:
            response = self.api_client.get(endpoint=endpoint, params=params)
            data = response
            spans_map = data['payload']['spans']
            return spans_map
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error occurred while fetching span maps from axon during API call: {e}")
            raise ClientInteractionException("Error while fetching spans Map",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             f"Error occurred during API call: {e}")

    def get_scenario_stats(self, scenario_id: str):
        endpoint = f"v1/c/axon/scenario"
        params = {"scenario_id_list": scenario_id, "st": "-12h"}
        try:
            response = self.api_client.get(endpoint=endpoint, params=params)
            data = response
            scenario_detail = data['payload']['scenarios']
            return scenario_detail
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error occurred while fetching scenario stats: {e}")
            raise ClientInteractionException("Error occurred while fetching scenario stats",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             str(e))

    def get_issue_summary(self, issue_id: str):
        endpoint = f"v1/c/axon/issue/{issue_id}"
        try:
            response = self.api_client.get(endpoint=endpoint)
            data = response
            issue_summary = data['payload']['issue']
            return issue_summary
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error occurred while fetching issue summary: {e}")
            raise ClientInteractionException("Error occurred while fetching issue summary",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             str(e))

    def get_pods_info(self, incident_id: str):
        endpoint = f"v1/c/axon/prom/pods-info/trace/{incident_id}"
        try:
            response = self.api_client.get(endpoint=endpoint)
            data = response
            pods_info = data['payload']['pods_info']
            return pods_info
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error occurred while fetching prometheus data: {e}")
            raise ClientInteractionException("Error occurred while fetching prometheus data",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             str(e))

    def get_prometheus_metric_data(self, prom_request_data: PromCustomMetricDataRequest):
        prom_id: str = "af3c874e-3932-4c61-823f-d470d7e8af54"  # fetch prom_id from redis TODO : fetch prometheus id from redis client
        endpoint = f"v1/c/axon/prom/{prom_id}/query"
        try:
            response = self.api_client.post(endpoint=endpoint, json=prom_request_data.to_dict())
            data = response
            prom_metric_data = data['payload']
            return prom_metric_data
        except requests.exceptions.RequestException as e:
            logger.error(log_tag, f"Error occurred while fetching prometheus custom metric data: {e}")
            raise ClientInteractionException("Error occurred while fetching prometheus custom metric data",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             str(e))
