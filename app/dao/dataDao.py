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


def get_and_sanitize_spans_map(issue_id, incident_id):
    spans_map = axon_svc_client.get_spans_map(issue_id, incident_id)
    for span_id in spans_map:
        span_raw_data = axon_svc_client.get_span_raw_data(issue_id, incident_id, span_id)
        if len(span_raw_data["req_body"]) > MAX_PAYLOAD_SIZE:
            span_raw_data["req_body"] = span_raw_data["req_body"][:MAX_PAYLOAD_SIZE]
        if len(span_raw_data["resp_body"]) > MAX_PAYLOAD_SIZE:
            span_raw_data["resp_body"] = span_raw_data["resp_body"][:MAX_PAYLOAD_SIZE]
        spans_map[span_id].update(span_raw_data)

    filtered_spans_map = dict()
    for spanId in spans_map:
        span = spans_map[spanId]
        # remove exception span from spanMap
        if str(span["protocol"]).upper() == "EXCEPTION":
            parentSpanId = span["parent_span_id"]
            if parentSpanId in spans_map:
                spans_map[parentSpanId]["exception"] = span["request_payload"]
                filtered_spans_map[parentSpanId] = spans_map[parentSpanId]
        else:
            filtered_spans_map[spanId] = span

    print(filtered_spans_map)

    return filtered_spans_map
