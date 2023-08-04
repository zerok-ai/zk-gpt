import client
import gpt
import config

GPTServiceProvider = gpt.GPTServiceProvider()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)


def getIssueSummary(issue_id):
    issueSummary = client.getIssueSummary(issue_id)
    gptInstance = GPTServiceProvider.registerGPTHandler(issue_id)

    gptInstance.setContext("An issue is defined as a group of incidents which are grouped by issue_title.")
    gptInstance.setContext("The following are the statistics for an issue:")
    gptInstance.setContext(issueSummary)

    question = "Summarise the issue statistics in above issue in 2 lines."
    answer = gptInstance.findAnswers(question)

    return answer


def getScenario(scenario_id):
    scenario_def = client.getScenario(scenario_id)
    scenario_stats = client.getScenarioStats(scenario_id)

    gptInstance = GPTServiceProvider.registerGPTHandler("scenario-"+scenario_id)

    gptInstance.setContext("A scenario is defined as a set of rules which are executed on network traces.")
    gptInstance.setContext("The following is the scenario definition containing the rules:")
    gptInstance.setContext(scenario_def)
    gptInstance.setContext("The following is the scenario statistics for the provided scenario:")
    gptInstance.setContext(scenario_stats)

    question = "Summarise the rules and the statistics features in above scenario in 2 lines."
    answer = gptInstance.findAnswers(question)

    return answer

def getIncidentRCA(issue_id, incident_id):
    spansMap = client.getSpansMap(issue_id, incident_id)
    for span_id in spansMap:
        spanRawData = client.getSpanRawdata(issue_id, incident_id, span_id)
        if len(spanRawData["request_payload"]) > MAX_PAYLOAD_SIZE:
            spanRawData["request_payload"] = spanRawData["request_payload"][:MAX_PAYLOAD_SIZE]
        if len(spanRawData["response_payload"]) > MAX_PAYLOAD_SIZE:
            spanRawData["response_payload"] = spanRawData["response_payload"][:MAX_PAYLOAD_SIZE]
        spansMap[span_id].update(spanRawData)
        del spansMap[span_id]["error"]

    print(spansMap)
    gptInstance = GPTServiceProvider.registerGPTHandler(issue_id + "-" + incident_id)

    gptInstance.setContext("We are using a json array to represent a network traces across different protocols.")
    gptInstance.setContext(
        "For the following json array containing request and response payloads for all spans for a trace, "
        "we will need to find the root cause")
    gptInstance.setContext(
        "The request and response payloads are truncated to " + str(MAX_PAYLOAD_SIZE) + " characters for brevity.")

    gptInstance.setContext("Following are the spans:")
    for spanId in spansMap:
        span = spansMap[spanId]
        span["span_id"] = spanId
        spanContext = str(span).replace(" ", "")
        gptInstance.setContext(spanContext)

    question = "Summarise the root cause of the issue in above trace in 2 lines."
    answer = gptInstance.findAnswers(question)

    print("Q:" + question)
    print("A:" + answer)
    return answer


def getIncidentQuery(issue_id, incident_id, query):
    if not GPTServiceProvider.hasHandler(issue_id + "-" + incident_id):
        return "Incident not found."

    gptInstance = GPTServiceProvider.registerGPTHandler(issue_id + "-" + incident_id)
    answer = gptInstance.findAnswers(query)

    print("Q:" + query)
    print("A:" + answer)

    return answer
