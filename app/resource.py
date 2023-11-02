from langchain.llms import OpenAI
import client
import gpt
import config
import gptLangchianInference
import pineconeInteraction
from clientServices import postgresClient
import dataDao
import event_type_handler
import inference_engine
import response_formatter

GPTServiceProvider = gpt.GPTServiceProvider()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)
langChainInferenceProvider = gptLangchianInference.LangChainInference()
pineconeInteractionProvider = pineconeInteraction.PineconeInteraction()


def getScenarioSummary(scenario_id):
    scenario_def = client.getScenario(scenario_id)
    scenario_stats = client.getScenarioStats(scenario_id)

    gptInstance = GPTServiceProvider.registerGPTHandler("scenario-" + scenario_id)

    gptInstance.setContext("A scenario is defined as a set of rules which are executed on network traces.")
    gptInstance.setContext("The following is the scenario definition containing the rules:")
    gptInstance.setContext(scenario_def)
    gptInstance.setContext("The following is the scenario statistics for the provided scenario:")
    gptInstance.setContext(scenario_stats)

    question = "Extract and Summarise the rules and the statistics of the above scenario in 2 lines."
    answer = gptInstance.findAnswers(question)

    return answer


def getIssueSummary(issue_id):
    issueSummary = client.getIssueSummary(issue_id)
    gptInstance = GPTServiceProvider.registerGPTHandler(issue_id)

    gptInstance.setContext(
        "An issue is defined as set of attributes separated by `¦` character. this convention is not to be part of summary")
    gptInstance.setContext("the issue in this case is " + str(issueSummary["issue_title"]))
    gptInstance.setContext("attributes include kubernetes namespace/service name and the issue type")
    gptInstance.setContext(
        "We have collected " + str(issueSummary["total_count"]) + " data samples for inference of this issue.")
    gptInstance.setContext("Data was collected from zeroK operator and kubernetes metrics server.")
    gptInstance.setContext(
        "To understand why a particular incident happened, click on any distinct incident on the right")

    question = "Summarize the issue in 2 lines including the number of data samples collected and the data sources."
    answer = gptInstance.findAnswers(question)

    return answer


def getAndSanitizeSpansMap(issue_id, incident_id):
    spansMap = client.getSpansMap(issue_id, incident_id)
    for span_id in spansMap:
        spanRawData = client.getSpanRawdata(issue_id, incident_id, span_id)
        if spanRawData is not None:
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

    print(filteredSpansMap)

    return filteredSpansMap


def getIncidentRCA(issue_id, incident_id, rcaUsingLangchianInference):
    # rcaUsingLangchianInference is true get infernce from langchain pipeline
    if rcaUsingLangchianInference:
        return get_incident_likely_cause(issue_id, incident_id, False)

    gptInstance = GPTServiceProvider.registerGPTHandler(issue_id + "-" + incident_id)

    gptInstance.setContext(
        "We are using a json array to represent a network traces and payload data across different protocols.")

    gptInstance.setContext(
        "The API is deployed in a kubernetes cluster whose state is defined as follows:")
    gptInstance.setContext("namespace: sofa-shop-mysql.")
    gptInstance.setContext("Services: (output of kubectl describe services -n sofa-shop-mysql")

    gptInstance.setContext(
        '''Service Name: availability, pods: 0/0, target:  http://availability.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext(
        '''Service Name: demo-shop-service, pods: 1/1, target: http://demo-shop-service.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext(
        ''' Service Name: inventory, pods: 1/1, target: http://inventory.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext('''Service Name: order, pods: 1/1, target: http://order.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext(
        '''Service Name: product, pods: 1/1, target: http://product.sofa-shop-mysql.svc.cluster.local''')

    gptInstance.setContext(
        "The API is deployed in a kubernetes cluster whose state is defined as follows:")
    gptInstance.setContext("namespace: sofa-shop-mysql.")
    gptInstance.setContext("Services: (output of kubectl describe services -n sofa-shop-mysql")

    # Uncomment this if the span data for availability service is available.
    # gptInstance.setContext('''Service Name: availability, pods: 0/0, target:  http://availability.sofa-shop-mysql.svc.cluster.local''')
    # gptInstance.setContext('''Service Name: demo-shop-service, pods: 1/1, target: http://demo-shop-service.sofa-shop-mysql.svc.cluster.local''')
    # gptInstance.setContext(''' Service Name: inventory, pods: 1/1, target: http://inventory.sofa-shop-mysql.svc.cluster.local''')
    # gptInstance.setContext('''Service Name: order, pods: 1/1, target: http://order.sofa-shop-mysql.svc.cluster.local''')
    # gptInstance.setContext('''Service Name: product, pods: 1/1, target: http://product.sofa-shop-mysql.svc.cluster.local''')

    gptInstance.setContext(
        '''If the response code is 502, attribute the issue to unavailable pods in 'availability' service in 'sofa-shop' namespace.''')

    gptInstance.setContext(
        "For the following json array containing request and response payloads for all spans for a trace, "
        "we will need to find the root cause")
    gptInstance.setContext(
        "The request and response payloads are truncated to " + str(MAX_PAYLOAD_SIZE) + " characters for brevity.")

    gptInstance.setContext("Following are the spans:")

    spansMap = getAndSanitizeSpansMap(issue_id, incident_id)
    spanList = []
    # provide spans as context
    for spanId in spansMap:
        span = spansMap[spanId]
        spanContext = str(span)
        spanList.append(spanContext)
        gptInstance.setContext(spanContext)

    question = "Summarise the root cause of the issue in above trace in 2 lines. including exception, infra or payload details needed to explain the cause of issue."
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


def get_issue_observation(issue_id, query):
    if not postgresClient.check_issue_presence_in_db(issue_id):
        pineconeInteractionProvider.vectorize_issue_and_pushtu_pinecone_db(issue_id)

    return pineconeInteractionProvider.get_gpt_inferences_for_query_custom_data(issue_id, query, 0.3, 30)


def get_issue_observation_with_params(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel, requestId):
    if not postgresClient.check_issue_presence_in_db(issue_id):
        pineconeInteractionProvider.vectorize_issue_and_pushtu_pinecone_db(issue_id)
    response = pineconeInteractionProvider.get_gpt_inferences_for_query_custom_data(issue_id, query, temperature, topK)
    postgresClient.insert_user_issue_inference(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel,
                                               requestId, response)
    return response


def update_user_issue_observation_feedback(requestId, feedback, score):
    print("Updating the User Feedback for the infernce with requestId : {requsetId}")
    postgresClient.update_user_inference_feedback(requestId, feedback, score)


def getAllIssueInferences(issue_id, limit, offset):
    print("Fetching all the inferences for the given issue id :{issue_id}")
    user_inferences = postgresClient.get_all_user_issue_inferences(issue_id, limit, offset)
    return user_inferences


def get_incident_likely_cause(issue_id, incident_id):
    if issue_id is None:
        raise Exception("issue_id is None")

    # regenerateRca = false check if rca already calculated for the issue send accordingly
    inference_db, incident_id_db = postgresClient.check_if_inference_already_present_for_issue(issue_id)

    if inference_db is not None and incident_id_db is not None:
        return issue_id, incident_id_db, response_formatter.get_formatted_inference_response(issue_id, incident_id_db,
                                                                                             inference_db)

    if incident_id is None or incident_id == "":
        # fetch latest incident_id for the issue
        incident_id = dataDao.get_latest_incident_id(issue_id)

    if incident_id is None:
        raise Exception("Given issue : {} doesn't have any trace ".format(issue_id))

    # # regenerateRca = false check if rca already calculated for the issue and incident and send accordingly
    # inference = postgresClient.check_if_inference_already_present(issue_id, incident_id)
    # # inference = None not present
    # if inference is None:
    inference = inference_engine.generate_and_store_inference(issue_id,
                                                              incident_id)  # check update or insert logic also

    return issue_id, incident_id, response_formatter.get_formatted_inference_response(issue_id, incident_id, inference)


def get_user_conversation_events(issue_id, limit, offset):
    total_count, user_conserve_events_response = postgresClient.get_user_conversation_events(issue_id, limit, offset)
    return total_count, user_conserve_events_response


def process_incident_event_and_get_event_response(issue_id, incident_id, event_type, event):
    # understand the event type
    # if event type is :
    # "QNA" then push fetch the context and fetch the pinecone vectors and also eventRequest as prompt to GPT
    # "INFERENCE" then fetch the langchain inference
    strategy_map = event_type_handler.strategy_map
    if event_type in strategy_map:
        strategy = strategy_map[event_type]
        return strategy.handle_event(issue_id, incident_id, event_type, event)
    else:
        raise Exception("Event type : {} is not supported".format(event_type))


def clear_slack_reporting():
    postgresClient.clear_slack_reporting_for_demo()


def clear_all_issue_data_for_demo():
    postgresClient.clear_all_issue_data_for_demo()
