import json

from codeinterpreterapi import CodeInterpreterSession
from langchain.chains import LLMMathChain
from langchain.output_parsers import ResponseSchema, StructuredOutputParser, PydanticOutputParser
from pydantic.v1 import BaseModel, Field, validator
from app.internal.langchain_adapter import langchain_adapter

from app import config
from app.models.enums.severity_enum import SeverityEnum
from app.models.llm_output_parser import PrometheusLLMOutputParser, PrometheusDataSummary

openai_api_key = config.configuration.get("openai_key", "")

response_schemas = [
    ResponseSchema(name="answer", description="answer to the user's question"),
    ResponseSchema(name="source", description="source used to answer the user's question, should be a website.")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()
Critical = "Urgently requires immediate attention"
Major = "Significant blocking problem that requires help"
Minor = "May be affecting customers, but no one is blocked"
Pending = "Severity to be decided and should be determined as soon as possible"
Normal = "No significant issues identified"
lang_chain_inference_provider = langchain_adapter.LangchainAdapter()


def analyse_metric_data(data):
    with CodeInterpreterSession(openai_api_key=openai_api_key) as session:
        # # define the user request
        # parser = PydanticOutputParser(pydantic_object=PrometheusDataSummary)
        # format_instructions = parser.get_format_instructions()
        # user_request = """When performing following query on prometheus: {query} with title description : {title} \
        # Received following data: {query_metric_data} Identify anomalies or issues present in the provided data \
        # Concisely within 2 or 3 lines, ensuring all key data points are addressed"""
        # # and what subsequent query can be made to prometheus to analyse this issue?
        #
        # temp: str = user_request.format(query=data['query'], title=data['title'],
        #                                 query_metric_data=data['query_metric_data'])
        #
        #
        # # generate the response
        #
        # assert session.agent_executor, "Session not initialized."
        # response = session.agent_executor.run(temp)
        # # prometheus_summary_resp = parser.parse(response)
        #
        # # output to the user
        # print("AI: ", response)
        #
        # return response

        # define the user request
        parser = PydanticOutputParser(pydantic_object=PrometheusDataSummary)
        format_instructions = parser.get_format_instructions()

        user_request = """When performing following query on prometheus: {query} with title description : {title} \ 
        Received following time series data: {query_metric_data}. I need assistance in Identify anomalies or issues \ 
        present in the provided data Concisely within 2 or 3 lines and also attach label based on the summary. \
        Generate response with formatted instruction as {format_instructions}. do not add any other elements to the \
        response."""

        temp: str = user_request.format(query=data['query'], title=data['title'],
                                        query_metric_data=data['query_metric_data'])

        # generate the response

        assert session.agent_executor, "Session not initialized."
        response = session.agent_executor.run(temp)
        # prometheus_summary_resp = parser.parse(response)

        # output to the user
        print("AI: ", response)

        return response


def analyse_metric_data_using_chain(data):
    llm_promql_queries_response = lang_chain_inference_provider.get_prometheus_data_summary_from_metric_data(
        data)
    parser = PydanticOutputParser(pydantic_object=PrometheusDataSummary)
    prom_summary = parser.parse(llm_promql_queries_response["prom_summary"])
    return prom_summary
