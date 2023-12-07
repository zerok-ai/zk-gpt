from typing import Any, Dict, List

from langchain.output_parsers import PydanticOutputParser

from app import config
from app.clients import axon_client
from app.internal.langchain_adapter import langchain_adapter
from app.internal.prometheus_adapter import promethus_metric_data_analyser
from app.models.prometheus_model import PrometheusLLMOutputQueries, PrometheusQueryMetricData, \
    PrometheusDataSummarySeverity, PrometheusQueryMetricDataSummarySeverity
from app.models.request.prom_custom_metric_data_request import PromCustomMetricDataRequest
from app.utils import zk_logger
from app.utils.utils import Utils

log_tag = "prometheus_adapter"
logger = zk_logger.logger

lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
openai_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index", "zk-index-prod")
pinecone_api_key = config.configuration.get("pinecone_key", "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment = config.configuration.get("pinecone_env", "us-west4-gcp-free")
user_qna_openai_temp = config.configuration.get("user_qna_openai_temp", 0.4)
user_qna_topk = config.configuration.get("user_qna_topk", 500)
axon_service_client = axon_client.AxonServiceClient()


def get_timestamp_and_duration_for_metric_query(start_time: str, end_time: str) -> tuple:
    try:
        if end_time == "0001-01-01T00:00:00Z":
            timestamp = Utils.get_epoch_current_timestamp()
            current_date_time = Utils.get_current_date_time_utc()
            # duration should be current datetime - start time - 10m
            duration = Utils.get_time_difference_in_minutes(start_time, current_date_time)
            duration += 10
            return timestamp, f"-{duration}m"
        else:
            timestamp = Utils.get_timestamp_from_datetime(end_time)
            duration = Utils.get_time_difference_in_minutes(start_time, end_time)
            duration += 10
            return timestamp, f"-{duration}m"
    except Exception as e:
        logger.error(log_tag,
                     f"An error occurred while generating timestamp and duration: star time: {start_time} and end time: {end_time}")
        timestamp = Utils.get_epoch_current_timestamp()
        duration = "-10m"
        return timestamp, duration


class PrometheusAdapter:

    def generate_prometheus_queries(self, custom_data):
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_langchain(custom_data)
        response = llm_promql_queries_response['promql_queries']
        print("llm promQL response :" + response)
        return response

    def generate_prometheus_queries_from_alert_definition(self, alert_definition) -> (
            List)[PrometheusQueryMetricDataSummarySeverity]:
        # create input variable for lang chain
        custom_data = {"alert_definition": str(alert_definition)}
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_from_prometheus_alert(
            custom_data)
        parser = PydanticOutputParser(pydantic_object=PrometheusLLMOutputQueries)
        prometheus_queries = parser.parse(llm_promql_queries_response["promql_queries"])
        # extract prom QL queries form LLM output and get metrics data for each metric from axon
        prometheus_queries_metrics_data: List[PrometheusQueryMetricData] = (
            self.fetch_prometheus_metric_data_for_each_query(
                prometheus_queries,
                alert_definition.get("startsAt", Utils.get_current_date_time_utc()),
                alert_definition.get("endsAt", Utils.get_current_date_time_utc())))

        prometheus_queries_metrics_data_analysis: List[PrometheusQueryMetricDataSummarySeverity] = []
        for prom_query_metric_data in prometheus_queries_metrics_data:
            # analyse each promQL query and metric data using LLM
            metric_data_analysis: PrometheusDataSummarySeverity = (
                promethus_metric_data_analyser.analyse_metric_data_using_chain(
                    prom_query_metric_data))
            # prom_query_metric_data.update(metric_data_analysis)
            # prom_query_metric_data.update({"metric_data_analysis": str(metric_data_analysis)})
            prometheus_queries_metrics_data_analysis.append(
                PrometheusQueryMetricDataSummarySeverity.get_prometheus_query_metric_data_summary_severity(
                    prom_query_metric_data, metric_data_analysis))
        return prometheus_queries_metrics_data_analysis

    def is_valid_prometheus_metric_data(self, prom_query_metric_data: Dict[str, Any]):
        # TODO:: validation of metric data
        pass

    def fetch_prometheus_metric_data_for_each_query(self, prometheus_queries_list: PrometheusLLMOutputQueries,
                                                    start_time: str, end_time: str) -> List[PrometheusQueryMetricData]:
        # fetch metrics data for each query
        prom_query_list = prometheus_queries_list.prom_query_list
        prometheus_queries_metric_data_list: List[PrometheusQueryMetricData] = []
        # get timestamp and duration from start time and end time
        # we will fetch prometheus metric data from current time stamp to the time 10 before the
        # start time considering the alert is firing state

        timestamp, duration = get_timestamp_and_duration_for_metric_query(start_time, end_time)
        for prom_query in prom_query_list:
            # for each query fetch metric data
            try:
                prom_custom_metric_data_request: PromCustomMetricDataRequest = PromCustomMetricDataRequest(
                    query=prom_query.query, time=timestamp, duration=duration)
                metrics_data = axon_service_client.get_prometheus_metric_data(prom_custom_metric_data_request)
                prom_metric_dict = {}
                prom_metric_dict.update(prom_query.to_dict())
                prom_metric_dict.update({"query_metric_data": str(metrics_data)})
                prometheus_queries_metric_data = PrometheusQueryMetricData.get_prometheus_query_metric_data(
                    prom_query, str(metrics_data))
                prometheus_queries_metric_data_list.append(prometheus_queries_metric_data)
            except Exception as e:
                logger.error(log_tag,
                             f"An error occurred while fetching metrics data for query: {prom_query} with "
                             f"error: {e}")

        return prometheus_queries_metric_data_list
