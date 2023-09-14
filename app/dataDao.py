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
import client
import config
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)


def get_latest_incident_id(issue_id):
    # fetch all incidents for the given issue
    issue_incidents = client.getIssueIncidents(issue_id)
    return issue_incidents[0]


def getRequestResponsePayload(issue_id,incident_id):
    return "request response payload"

def getCpuUsageData():
    return ""


def getMemoryUsage():
    return ""

def getPodInfo():
    return ""

def getDeploymentInfo():
    return ""

def getTraceSpanData(issue_id,incident_id):
    spansMap = client.getSpansMap(issue_id, incident_id)
    for span_id in spansMap:
        spanRawData = client.getSpanRawdata(issue_id, incident_id, span_id)
        if len(spanRawData["req_body"]) > MAX_PAYLOAD_SIZE:
            spanRawData["req_body"] = spanRawData["req_body"][:MAX_PAYLOAD_SIZE]
        if len(spanRawData["resp_body"]) > MAX_PAYLOAD_SIZE:
            spanRawData["resp_body"] = spanRawData["resp_body"][:MAX_PAYLOAD_SIZE]
        spansMap[span_id].update(spanRawData)

    filteredSpansMap = dict()
    for spanId in spansMap:
        span = spansMap[spanId]
        # remove exception span from spanMap
        if str(span["protocol"]).upper() == "EXCEPTION":
            parentSpanId = span["parent_span_id"]
            if parentSpanId in spansMap:
                spansMap[parentSpanId]["exception"] = span["request_payload"]
                filteredSpansMap[parentSpanId] = spansMap[parentSpanId]
        else:
            filteredSpansMap[spanId] = span

    return filteredSpansMap

def getIssueData():
    print("temp")


def getPrometheusData(issue_id,incident_id): 
    print("temp")




