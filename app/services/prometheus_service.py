from langchain.output_parsers import EnumOutputParser

from app import config
from app import gpt
from app.clientServices import postgresClient
from app.clients import axon_client, redis_client
from app.dao import dataDao
from app.internal.inference_adapter import inference_adapter
from app.internal.langchain_adapter import langchain_adapter
from app.internal.prometheus_adapter import prometheus_adapter
from app.internal.pinecone_adapter import pinecone_adapter
from app.models.response.incident_rca_response import IncidentRcaResponse
from app.services import inference_service
from app.utils import zk_logger

GPTServiceProvider = gpt.GPTServiceProvider()
MAX_PAYLOAD_SIZE = config.configuration.get("max_span_raw_data_length", 100)
lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
prom_adapter_provider = prometheus_adapter.PrometheusAdapter()
pinecone_interaction_provider = pinecone_adapter.PineconeAdapter()
axon_svc_client = axon_client.AxonServiceClient()
redis_svc_client = redis_client.RedisServiceClient()
inference_service_impl = inference_service.InferenceService()
inference_adapter_impl = inference_adapter.InferenceAdapter()
log_tag = "issue_service"
logger = zk_logger.logger


class PrometheusService:

    def get_prometheus_report(self, issue_id, incident_id):
        # fetch relevant data using axon api
        pods_info = axon_svc_client.get_pods_info(incident_id)

        #  fetch issue title and inference from db
        inference, issue_title = postgresClient.check_if_inference_already_present(issue_id, incident_id)

        if inference is None:
            inference = inference_adapter_impl.generate_and_store_inference(issue_id,
                                                                            incident_id)

        if issue_title is None:
            issue_summary = axon_svc_client.get_issue_summary(issue_id)
            issue_title = str(issue_summary["issue_title"])

        # create input variable for lang chain
        custom_data = {"issue_title": str(issue_title), "issue_inference": str(inference),
                       "data": str(pods_info)}
        # "issue_prompt": "You are an on-call engineer help in constructing promQL queries for
        # relevant metrics that you as an on-call engineer would look at to root-cause the issue"

        print("custom_data" + str(custom_data))
        # generate prometheus queries

        prometheus_queries = prom_adapter_provider.generate_prometheus_queries(custom_data)

        print("prometheus_queries: \n" + str(prometheus_queries))

        return prometheus_queries

    def get_prometheus_queries_from_alert_definition(self, alert_definition):
        prometheus_queries = prom_adapter_provider.generate_prometheus_queries_from_alert_definition(alert_definition)
        # TODO :: promQL store in DB using sqlalchemy
        return prometheus_queries
