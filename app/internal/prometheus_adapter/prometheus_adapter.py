import json

from app import config
from app.internal.langchain_adapter import langchain_adapter
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


class PrometheusAdapter:

    def generate_prometheus_queries(self, custom_data):
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_langchain(custom_data)
        response = llm_promql_queries_response['promql_queries']
        print("llm promQL response :" + response)
        return response

    def generate_prometheus_queries_from_alert_defination(self, alert_definition):
        # create input variable for langchain
        custom_data = {"alert_definition": str(alert_definition)}
        llm_promql_queries_response = lang_chain_inference_provider.get_promql_queries_from_prometheus_alert(
            custom_data)
        response = llm_promql_queries_response['promql_queries']
        print("llm promQL response :" + response)
        return response
