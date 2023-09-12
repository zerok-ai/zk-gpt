from langchain.llms import OpenAI
import client
import gpt
import config
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
import gptLangchianInference
import pineconeInteraction
from clientServices import postgresClient

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


def getIncidentRCA(issue_id, incident_id):
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

    # lang chain integration

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

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "We are using a json array to represent a network traces and payload data across different protocols."
                    "The API is deployed in a kubernetes cluster whose state is defined as follows:"
                    "namespace: sofa-shop-mysql."
                    "Services: (output of kubectl describe services -n sofa-shop-mysql"
                    '''Service Name: availability, pods: 0/0, target:  http://availability.sofa-shop-mysql.svc.cluster.local'''
                    '''Service Name: demo-shop-service, pods: 1/1, target: http://demo-shop-service.sofa-shop-mysql.svc.cluster.local'''
                    ''' Service Name: inventory, pods: 1/1, target: http://inventory.sofa-shop-mysql.svc.cluster.local'''
                    '''Service Name: order, pods: 1/1, target: http://order.sofa-shop-mysql.svc.cluster.local'''
                    '''Service Name: product, pods: 1/1, target: http://product.sofa-shop-mysql.svc.cluster.local'''
                    '''If the response code is 502, attribute the issue to unavailable pods in 'availability' service in 'sofa-shop' namespace.'''
                    "For the following json array containing request and response payloads for all spans for a trace, "
                    "we will need to find the root cause"
                    "The request and response payloads are truncated to 1000 characters for brevity."
                    "Following are the spans:"
                    "{spans}"

                )
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
    )

    llm = OpenAI(model_name="gpt-3.5-turbo")
    res = llm(template.format_messages(spans=spanList,
                                       text='Summarise the root cause of the issue in above trace in 2 lines. including exception, infra or payload details needed to explain the cause of issue.'))

    print("\n --------------------LANGCHAIN---------------------------------------")
    print(res)
    print("\n ------------------------------------------------------------------------------------------------")

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


def getIssueObservation(issue_id, query):
    if not postgresClient.findIfIssueIsPresentInDb(issue_id):
        pineconeInteractionProvider.vectorizeIssueAndPushtoPineconeDb(issue_id)

    return pineconeInteractionProvider.getGptInferencesForQueryCustomData(issue_id, query, 0.3, 30)


def getIssueObservationWithParams(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel, requestId):
    if not postgresClient.findIfIssueIsPresentInDb(issue_id):
        pineconeInteractionProvider.vectorizeIssueAndPushtoPineconeDb(issue_id)
    response = pineconeInteractionProvider.getGptInferencesForQueryCustomData(issue_id, query, temperature, topK)
    postgresClient.insertUserIssueInference(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel,
                                            requestId, response)
    return response


def updateUserIssueObservationFeedback(requestId, feedback, score):
    print("Updating the User Feedback for the infernce with requestId : {requsetId}")
    postgresClient.updateUserInferenceFeedback(requestId, feedback, score)


def getAllIssueInferences(issue_id, limit, offset):
    print("Fetching all the inferences for the given issue id :{issue_id}")
    user_inferences = postgresClient.getAllUserIssueInferences(issue_id, limit, offset)
    return user_inferences


def getIssueIncidentRca(issue_id, incident_id, regenerateRca):
    # This call is at issue level only not at incident level
    # check in DB if present just send.
    if regenerateRca:
        isRca, answer = postgresClient.checkIfRcaAlreadyGenerated(issue_id, incident_id)
        print("Got request to regenerate RCA for issue : {} and incident: {}".format(issue_id, incident_id))
        # check dedup request in DB
        if isRca:
            return answer
        else:
            # generate RCA and sned the respone and store in DB and pinecone
            rca = generateAndStoreRca(issue_id, incident_id)  # check update or insert logic also
            return rca
    else:
        # regenerateRca = false check if rca already calculated for the issue and send accordindly
        answer = postgresClient.checkIfRcaAlreadyPresent(issue_id)
        if answer is None:
            rca = generateAndStoreRca(issue_id, incident_id)  # check update or insert logic also
            return rca
        else:
            return answer


def generateAndStoreRca(issue_id, incident_id):
    # getting langchain inferences
    custom_data, langchianInference = getLangchainInference(issue_id, incident_id)
    rca = langchianInference['final_summary']
    # push data to pinecone
    pineconeIssueData = dict()
    pineconeIssueData['issue_data'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id, "data",
                                                                                     "issue", custom_data['issue_data'],
                                                                                     "default", "default")
    pineconeIssueData['trace_data'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id, "data",
                                                                                     "trace", custom_data['trace_data'],
                                                                                     "default", "default")
    pineconeIssueData['exception_data'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id, "data",
                                                                                         "exception",
                                                                                         custom_data['exception_data'],
                                                                                         "default", "default")
    pineconeIssueData['req_res_data'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id, "data",
                                                                                       "req_res",
                                                                                       custom_data['req_res_data'],
                                                                                       "default", "default")
    pineconeIssueData['final_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
                                                                                        "summary", "final",
                                                                                        langchianInference[
                                                                                            'final_summary'], "default",
                                                                                        "default")
    pineconeIssueData['exception_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
                                                                                            "summary", "exception",
                                                                                            langchianInference[
                                                                                                'exception_summary'],
                                                                                            "default", "default")
    pineconeIssueData['trace_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
                                                                                        "summary", "trace",
                                                                                        langchianInference[
                                                                                            'trace_summary'], "default",
                                                                                        "default")
    pineconeIssueData['issue_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
                                                                                        "summary", "issue",
                                                                                        langchianInference[
                                                                                            'issue_summary'], "default",
                                                                                        "default")
    data_list = [value for value in pineconeIssueData.values()]
    pineconeInteractionProvider.vectorizeDataAndPushtoPineconeDB(issue_id, incident_id, data_list)
    # store in DB
    postgresClient.insertOrUpdateRcaToDB(issue_id, incident_id, rca)
    return rca


def getLangchainInference(issue_id, incident_id):
    # fetch all the data required for langchian inference
    issueSummary = client.getIssueSummary(issue_id)
    spansMap = client.getSpansMap(issue_id, incident_id)
    exceptionMap = []
    reqResPayloadMap = []
    for span_id in spansMap:
        spanRawData = client.getSpanRawdata(issue_id, incident_id, span_id)
        spansMap[span_id].update(spanRawData)

    filteredSpansMap = dict()
    for spanId in spansMap:
        # remove error key from spanMap
        del spansMap[spanId]["error"]

        span = spansMap[spanId]
        span["span_id"] = spanId
        # remove exception span from spanMap
        if str(span["protocol"]).upper() == "EXCEPTION":
            parentSpanId = span["parent_span_id"]
            if parentSpanId in spansMap:
                spansMap[parentSpanId]["exception"] = span["req_body"]
                exceptionMap.append(span["req_body"])
                filteredSpansMap[parentSpanId] = spansMap[parentSpanId]
        else:
            filteredSpansMap[spanId] = span

    for spanId in filteredSpansMap:
        span = spansMap[spanId]
        reqResPayloadMap.append({"request_payload": span['req_body'], "span": spanId})
        reqResPayloadMap.append({"response_payload": span['resp_body'], "span": spanId})

    # create input variabled for langchain
    custom_data = {"issue_data": str(issueSummary), "trace_data": str(filteredSpansMap),
                   "exception_data": str(exceptionMap), "req_res_data": str(reqResPayloadMap),
                   "issue_prompt": "You are a backend developer AI assistant. Your task is to figure out why an issue happened and present it in a concise manner."}

    # get langchain inference
    langchianInference = langChainInferenceProvider.getGPTLangchainInference(issue_id, incident_id, custom_data)

    return custom_data, langchianInference
