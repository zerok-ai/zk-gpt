import client
import json
import gptLangchianInference
import pineconeInteraction
import slack_integration
from clientServices import postgresClient
from datetime import datetime

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client import generate_latest
from io import BytesIO

langChainInferenceProvider = gptLangchianInference.LangChainInference()


def generate_prometheus_queries(custom_data):
    llm_promql_queries_response = langChainInferenceProvider.get_promql_queries_langchain(custom_data)
    response = llm_promql_queries_response['promql_queries']
    print("llm promQL response :" + response)

    # Parse the JSON string into a Python list
    python_list = json.loads(response)
    new_list = [s.replace('\\"', '"') for s in python_list]

    # Now, python_list contains the list of strings
    print("llm promQL response :" + str(new_list))


    # Convert the string to a Metric Family
    metric_families = list(text_string_to_metric_families(promql_string))

    # Generate a Prometheus metric
    metrics_output = BytesIO()
    generate_latest(metrics_output, metric_families=metric_families)
    promql_query = metrics_output.getvalue().decode("utf-8")

    print(promql_query)

    return new_list
