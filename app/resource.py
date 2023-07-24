import client
import gpt
import config

GPTServiceProvider = gpt.GPTServiceProvider()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)


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

    question = "What seems to be the issue in above trace?"
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
