from langchain.output_parsers import PydanticOutputParser

from app import config
from app.clients import axon_client
from app.internal.langchain_adapter import langchain_adapter
from app.internal.prometheus_adapter import promethus_metric_data_analyser
from app.models.llm_output_parser import PrometheusLLMOutputParser
from app.models.request.prom_custom_metric_data_request import PromCustomMetricDataRequest
from app.utils import zk_logger

log_tag = "pinecone_adapter"
logger = zk_logger.logger

lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
openai_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index", "zk-index-prod")
pinecone_api_key = config.configuration.get("pinecone_key", "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment = config.configuration.get("pinecone_env", "us-west4-gcp-free")
user_qna_openai_temp = config.configuration.get("user_qna_openai_temp", 0.4)
user_qna_topk = config.configuration.get("user_qna_topk", 500)
axon_service_client = axon_client.AxonServiceClient()


class PrometheusAdapter:

    def generate_prometheus_queries(self, custom_data):
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_langchain(custom_data)
        response = llm_promql_queries_response['promql_queries']
        print("llm promQL response :" + response)
        return response

    def generate_prometheus_queries_from_alert_definition(self, alert_definition):
        # create input variable for langchain
        custom_data = {"alert_definition": str(alert_definition)}
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_from_prometheus_alert(
            custom_data)
        parser = PydanticOutputParser(pydantic_object=PrometheusLLMOutputParser)
        prometheus_queries = parser.parse(llm_promql_queries_response["promql_queries"])
        # analyse prom QL queries and get metrics data for each metric from axon
        prometheus_queries_metrics_data = self.fetch_and_analyse_prom_queries_data(prometheus_queries)
        prometheus_queries_metrics_data_analysis = []
        for prom_query_metric_data in prometheus_queries_metrics_data:
            metric_data_analysis = promethus_metric_data_analyser.analyse_metric_data_using_chain(prom_query_metric_data)
            prom_query_metric_data.update(metric_data_analysis)
            prom_query_metric_data.update({"metric_data_analysis": str(metric_data_analysis)})
            prometheus_queries_metrics_data_analysis.append(prom_query_metric_data)

        return prometheus_queries_metrics_data_analysis

        # and then give that data to code completion llm model with different tags
        # and analyse accordingly

    def fetch_and_analyse_prom_queries_data(self, prometheus_queries_list: PrometheusLLMOutputParser):
        # fetch metrics data for each query
        prom_query_list = prometheus_queries_list.prom_query_list
        prometheus_queries_metric_data_list = []
        timestamp = 1700812681
        for prom_query in prom_query_list:
            # for each query fetch metric data
            try:
                prom_custom_metric_data_request: PromCustomMetricDataRequest = PromCustomMetricDataRequest(
                    query=prom_query.query, time=timestamp, duration="-5m")
                metrics_data = axon_service_client.get_prometheus_metric_data(prom_custom_metric_data_request)
                prom_metric_dict = {}
                prom_metric_dict.update(prom_query.to_dict())
                prom_metric_dict.update({"query_metric_data": str(metrics_data)})
                prometheus_queries_metric_data_list.append(prom_metric_dict)
            except Exception as e:
                print(f"error for query: %s", str(prom_query))

        return prometheus_queries_metric_data_list
