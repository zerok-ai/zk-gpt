"""
CLASS OVERVIEW 
INPUT : request for the data across different datasets 

things it does : 
interacts with different clients, DB ,Axon etc 
1) fetch the specific requested data 

OUTPUT : returns the requested data across different datasets

1) get issue data 
2) get trace data 
3) get spans 
4) get request and response 
5) get prom CPU data 
6) get memory data 
7) get pod info 
8) get pod status 
9) get logs <backlog>
"""
import config

from app.clients import axon_client

MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)
axon_svc_client = axon_client.AxonServiceClient()


def get_latest_incident_id(issue_id):
    # fetch all incidents for the given issue
    issue_incidents = axon_svc_client.get_issue_incidents(issue_id)
    return issue_incidents[0]


def get_request_response_payload(issue_id, incident_id):
    return "request response payload"


def get_cpu_usage_data():
    return ""


def get_memory_usage():
    return ""


def get_pod_info():
    return ""


def get_deployment_info():
    return ""

