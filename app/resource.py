import json
from flask import jsonify
from langchain.llms import OpenAI 
import client
import gpt
import gptInferencePinecone
import config

GPTServiceProvider = gpt.GPTServiceProvider()
GptInferencePineconeVectorDb = gptInferencePinecone.GptInferencePineconeVectorDb()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)
# langChainInference = gptLangchianInference.LangChainInference

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

    gptInstance.setContext("An issue is defined as set of attributes separated by `¦` character. this convention is not to be part of summary")
    gptInstance.setContext("the issue in this case is " + str(issueSummary["issue_title"]))
    gptInstance.setContext("attributes include kubernetes namespace/service name and the issue type")
    gptInstance.setContext("We have collected " + str(issueSummary["total_count"]) + " data samples for inference of this issue.")
    gptInstance.setContext("Data was collected from zeroK operator and kubernetes metrics server.")
    gptInstance.setContext("To understand why a particular incident happened, click on any distinct incident on the right")

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

    gptInstance.setContext('''Service Name: availability, pods: 0/0, target:  http://availability.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext('''Service Name: demo-shop-service, pods: 1/1, target: http://demo-shop-service.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext(''' Service Name: inventory, pods: 1/1, target: http://inventory.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext('''Service Name: order, pods: 1/1, target: http://order.sofa-shop-mysql.svc.cluster.local''')
    gptInstance.setContext('''Service Name: product, pods: 1/1, target: http://product.sofa-shop-mysql.svc.cluster.local''')

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
    res = llm(template.format_messages(spans = spanList ,text='Summarise the root cause of the issue in above trace in 2 lines. including exception, infra or payload details needed to explain the cause of issue.'))

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

def getIssueObservation(issue_id,query):
    if not client.findIfIssueIsPresentInDb(issue_id): 
        GptInferencePineconeVectorDb.vectorizeIncidentAndPushtoVectorDb(issue_id)

    return GptInferencePineconeVectorDb.getGptInferencesForQuery(issue_id,query,0.3,30)
    
def getIssueObservationWithParams(issue_id, query,temperature,topK,vectorEmbeddingModel,gptModel,requestId):
    if not client.findIfIssueIsPresentInDb(issue_id):
        GptInferencePineconeVectorDb.vectorizeIncidentAndPushtoVectorDb(issue_id)
    response =  GptInferencePineconeVectorDb.getGptInferencesForQuery(issue_id,query,temperature,topK)    
    client.insertUserIssueInference(issue_id, query,temperature,topK,vectorEmbeddingModel,gptModel,requestId,response)
    return response 
    
def updateUserIssueObservationFeedback(requestId,feedback,score): 
    print("Updating the User Feedback for the infernce with requestId : {requsetId}")
    client.updateUserInferenceFeedback(requestId,feedback,score)

def getAllIssueInferences(issue_id,limit,offset): 
    print("Fetching all the inferences for the given issue id :{issue_id}")
    userInferences = client.getAllUserIssueInferences(issue_id,limit,offset)
    return userInferences

# def getZerokIssueIncidentInference(issue_id,incident_id):
    print("Starting the zerok inference for  issue id :{issue_id}")

    data = {
            "span_data" : None,
            "req_res_data": None,
            "prom_data": None,
            "issue_data": None,
        }

    try:
        # check in postgress if the issue is already inferenced 
        # if yes send data directly from postgress 
        dbInferenceData = client.findIfIssueIncidentIsPresentInDb(issue_id,incident_id)
        if dbInferenceData != False:
            return dbInferenceData   #modify the logic to send only the inference
        
        # if no genereate the inference and store in postgress for future reference 
        # fetching all the issue data using different API's 
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Define functions to call concurrently
            span_data_future = executor.submit(dataDao.getTraceSpanData, issue_id, incident_id)
            request_response_payload_future = executor.submit(dataDao.getRequestResponsePayload, issue_id, incident_id)
            prometheus_data_future = executor.submit(dataDao.getPrometheusData, issue_id, incident_id)
            issue_data_future = executor.submit(dataDao.getIssueData, issue_id, incident_id)

            # Wait for all futures to complete
            concurrent.futures.wait([span_data_future, request_response_payload_future, prometheus_data_future, issue_data_future])

            # Get results or handle exceptions
            span_data = span_data_future.result()
            request_response_payload = request_response_payload_future.result()
            prometheus_data = prometheus_data_future.result()
            issue_data = issue_data_future.result()

        # Handle data or exceptions here
        if span_data is not None and request_response_payload is not None:
            # Process span_data and request_response_payload
            data['span_data'] =span_data
        else:
            # Handle missing data or exceptions
            data["span_data"] = None

        if prometheus_data is not None:
            cpu_usage_data, memory_usage_data, pod_info_data, deployment_info_data, config_map_info_data = prometheus_data
            # Process CPU, memory, pod, deployment, and config map data
            data['prom_data'] =prometheus_data
        else:
            # Handle missing prometheus data or exceptions
            data['prom_data'] =None

        if issue_data is not None:
            # Process issue_data
            data['issue_data'] =issue_data
        else:
            # Handle missing prometheus data or exceptions
            data['issue_data'] =None
        
    
        # using langchain to get inference the issue data 
        gptLangchainIssueInference = langChainInference.getGPTLangchainInference(issue_id,incident_id,data)
        # store the inference and data in pinecone 
        pineconeInteraction.ingestIssueDataToPinecone(data,gptLangchainIssueInference,issue_id,incident_id)
        #  and store the meta information in DB 
        client.ingestGptLangChainInference(issue_id,incident_id,gptLangchianInference)
        # return the data
        return gptLangchainIssueInference

    except Exception as e:
        print(f"An error occurred: {e}")

    


   