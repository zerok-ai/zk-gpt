import config
from app import gpt
from app.clients import axon_client, redis_client
from app.dao import dataDao
from app.internal.langchain_adapter import langchain_adapter
from app.internal.pinecone_adapter import pinecone_adapter
from app.models.response.incident_rca_response import IncidentRcaResponse
from app.services import inference_service
from app.utils import zk_logger

GPTServiceProvider = gpt.GPTServiceProvider()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)
lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
pinecone_interaction_provider = pinecone_adapter.PineconeAdapter()
axon_svc_client = axon_client.AxonServiceClient()
redis_svc_client = redis_client.RedisServiceClient()
inference_service_impl = inference_service.InferenceService()
log_tag = "issue_service"
logger = zk_logger.logger


class IssueService:

    def get_scenario_summary(self, scenario_id: str):
        scenario_def = redis_svc_client.get_scenario(scenario_id)
        scenario_stats = axon_svc_client.get_scenario_stats(scenario_id)

        gpt_instance = GPTServiceProvider.registerGPTHandler("scenario-" + scenario_id)

        gpt_instance.setContext("A scenario is defined as a set of rules which are executed on network traces.")
        gpt_instance.setContext("The following is the scenario definition containing the rules:")
        gpt_instance.setContext(scenario_def)
        gpt_instance.setContext("The following is the scenario statistics for the provided scenario:")
        gpt_instance.setContext(scenario_stats)

        question = "Extract and Summarise the rules and the statistics of the above scenario in 2 lines."
        answer = gpt_instance.findAnswers(question)

        return answer

    def get_issue_summary(self, issue_id: str):
        issue_summary = axon_svc_client.get_issue_summary(issue_id)
        gpt_instance = GPTServiceProvider.registerGPTHandler(issue_id)

        gpt_instance.setContext(
            "An issue is defined as set of attributes separated by `¦` character. this convention is not to be part of summary")
        gpt_instance.setContext("the issue in this case is " + str(issue_summary["issue_title"]))
        gpt_instance.setContext("attributes include kubernetes namespace/service name and the issue type")
        gpt_instance.setContext(
            "We have collected " + str(issue_summary["total_count"]) + " data samples for inference of this issue.")
        gpt_instance.setContext("Data was collected from zeroK operator and kubernetes metrics server.")
        gpt_instance.setContext(
            "To understand why a particular incident happened, click on any distinct incident on the right")

        question = "Summarize the issue in 2 lines including the number of data samples collected and the data sources."
        answer = gpt_instance.findAnswers(question)

        return answer

    def get_incident_rca(self, issue_id, incident_id, rca_using_langchain_inference) -> IncidentRcaResponse:
        # rcaUsingLangchianInference is true get infernce from langchain pipeline
        if rca_using_langchain_inference:
            return inference_service_impl.get_incident_likely_cause(issue_id, incident_id, False)

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
        gptInstance.setContext(
            '''Service Name: order, pods: 1/1, target: http://order.sofa-shop-mysql.svc.cluster.local''')
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

        spans_map = dataDao.get_and_sanitize_spans_map(issue_id, incident_id)
        span_list = []
        # provide spans as context
        for spanId in spans_map:
            span = spans_map[spanId]
            span_context = str(span)
            span_list.append(span_context)
            gptInstance.setContext(span_context)

        question = "Summarise the root cause of the issue in above trace in 2 lines. including exception, infra or payload details needed to explain the cause of issue."
        answer = gptInstance.findAnswers(question)
        incident_rca_response = IncidentRcaResponse(rca=answer)
        logger.info(log_tag, "Q:" + question)
        logger.info(log_tag, "A:" + answer)
        return incident_rca_response

    def get_incident_query(self, issue_id, incident_id, query):
        if not GPTServiceProvider.hasHandler(issue_id + "-" + incident_id):
            return "Incident not found."

        gpt_instance = GPTServiceProvider.registerGPTHandler(issue_id + "-" + incident_id)
        answer = gpt_instance.findAnswers(query)

        logger.info(log_tag, "Q:" + query)
        logger.info(log_tag, "A:" + answer)

        return answer

