from datetime import datetime
from typing import Dict

from fastapi import status

from app.clientServices import postgresClient
from app.clients import axon_client
from app.exceptions.exception import InferenceGenerationException
from app.internal.langchain_adapter import langchain_adapter
from app.internal.pinecone_adapter import pinecone_adapter
from app.services import slack_service
from app.utils import zk_logger

lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
pinecone_interaction_provider = pinecone_adapter.PineconeAdapter()
axon_svc_client = axon_client.AxonServiceClient()
slack_service_impl = slack_service.SlackService()
log_tag = "inference_adapter"
logger = zk_logger.logger


class InferenceAdapter:
    def generate_and_store_inference(self, issue_id: str, incident_id: str):
        # getting langchain inferences
        issue_summary = axon_svc_client.get_issue_summary(issue_id)
        custom_data, langchain_inference = self.get_langchain_inference(issue_id, incident_id, issue_summary)
        inference = langchain_inference['final_summary']

        # vectorize data and push to pinecone
        self.vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchain_inference, custom_data)

        issue_title = issue_summary['issue_title']
        issue_last_seen = self.get_time_stamp_from_datatime(issue_summary['last_seen'])
        issue_first_seen = self.get_time_stamp_from_datatime(issue_summary['first_seen'])

        # store in DB
        postgresClient.insert_or_update_inference_to_db(issue_id, incident_id, inference, issue_title, issue_last_seen,
                                                        issue_first_seen)

        logger.info(log_tag, f"stored inference in DB for issue: {issue_id} and incidentId: {incident_id}")
        # slack integration
        slack_service_impl.store_inference_for_reporting(issue_id, incident_id, issue_last_seen)

        return inference

    def generate_and_store_inference_for_scheduler(self, issue_id: str, incident_id: str, issue_data):
        issue_last_seen = self.get_time_stamp_from_datatime(issue_data["last_seen"])
        issue_first_seen = self.get_time_stamp_from_datatime(issue_data["first_seen"])

        logger.info(log_tag, f"last seen: {str(issue_last_seen)}")

        # getting langchain inferences
        issue_summary = axon_svc_client.get_issue_summary(issue_id)

        custom_data, langchain_inference = self.get_langchain_inference(issue_id, incident_id, issue_summary)

        inference = langchain_inference['final_summary']

        # vectorize data and push to pinecone
        self.vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchain_inference, custom_data)

        issue_title = issue_summary['issue_title']

        logger.info(log_tag, f"inference genereted succesfully for {issue_id} and now we are storign in DB")

        # store in DB
        postgresClient.insert_or_update_inference_to_db(issue_id, incident_id, inference, issue_title, issue_last_seen,
                                                        issue_first_seen)

        logger.info(log_tag, f"stored inference in DB for issue: {issue_id} and incidentId: {incident_id}")
        # slack integration
        slack_service_impl.store_inference_for_reporting(issue_id, incident_id, issue_last_seen)

        return inference

    def get_langchain_inference(self, issue_id: str, incident_id: str, issue_summary: str):
        # fetch all the data required for langchain inference
        logger.info(log_tag, "starting langchain inference: ")
        spans_map = axon_svc_client.get_spans_map(issue_id, incident_id)
        exception_map = []
        req_res_payload_map = []
        for span_id in spans_map:
            span_raw_data = axon_svc_client.get_span_raw_data(issue_id, incident_id, span_id)
            if span_raw_data is not None:
                spans_map[span_id].update(span_raw_data)

        filtered_spans_map = dict()
        for spanId in spans_map:
            # remove error key from spanMap
            del spans_map[spanId]["error"]

            span = spans_map[spanId]
            span["span_id"] = spanId
            # remove exception span from spanMap
            if str(span["protocol"]).upper() == "EXCEPTION" or str(span["path"]).upper() == "/EXCEPTION":
                parent_span_id = span["parent_span_id"]
                exception_map.append(span.get("req_body"))
                if parent_span_id in spans_map:
                    spans_map[parent_span_id]["exception"] = span.get("req_body")
                    filtered_spans_map[parent_span_id] = spans_map[parent_span_id]
            else:
                filtered_spans_map[spanId] = span

        for spanId in filtered_spans_map:
            span = spans_map[spanId]
            req_res_payload_map.append({"request_payload": span.get('req_body'), "span": spanId})
            req_res_payload_map.append({"response_payload": span.get('resp_body'), "span": spanId})

        # create input variable for langchain
        custom_data = {"issue_data": str(issue_summary["issue_title"]), "trace_data": str(filtered_spans_map),
                       "exception_data": str(exception_map), "req_res_data": str(req_res_payload_map),
                       "issue_prompt": "You are a backend developer AI assistant. Your task is to figure out why an issue happened based the exception,trace,request respone payload data's presented to you in langchain sequential chain manner, and present it in a concise manner."}

        # get langchain inference
        langchain_inference = lang_chain_inference_provider.get_gpt_langchain_inference(issue_id, incident_id, custom_data)

        return custom_data, langchain_inference

    def vectorize_inference_data_and_push_to_pinecone(self, issue_id: str, incident_id: str, langchian_inference, custom_data: Dict[str, str]):
        # push data to pinecone
        pinecone_issue_data = dict()
        pinecone_issue_data['issue_data'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                             "data",
                                                                                             "issue",
                                                                                               custom_data['issue_data'],
                                                                                             "default", "default")
        pinecone_issue_data['trace_data'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                             "data",
                                                                                             "trace",
                                                                                               custom_data['trace_data'],
                                                                                             "default", "default")
        pinecone_issue_data['exception_data'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                                 "data",
                                                                                                 "exception",
                                                                                                   custom_data[
                                                                                                     'exception_data'],
                                                                                                 "default", "default")
        pinecone_issue_data['req_res_data'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                               "data",
                                                                                               "req_res",
                                                                                                 custom_data[
                                                                                                   'req_res_data'],
                                                                                               "default", "default")
        pinecone_issue_data['req_res_summary'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                                  "summary", "req_res",
                                                                                                    langchian_inference[
                                                                                                      'req_res_summary'],
                                                                                                  "default",
                                                                                                  "default")
        pinecone_issue_data['final_summary'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                                "summary", "final",
                                                                                                  langchian_inference[
                                                                                                    'final_summary'],
                                                                                                "default",
                                                                                                "default")
        pinecone_issue_data['exception_summary'] = pinecone_interaction_provider.create_pinecone_data(issue_id,
                                                                                                      incident_id,
                                                                                                    "summary",
                                                                                                    "exception",
                                                                                                      langchian_inference[
                                                                                                        'exception_summary'],
                                                                                                    "default",
                                                                                                    "default")
        pinecone_issue_data['trace_summary'] = pinecone_interaction_provider.create_pinecone_data(issue_id, incident_id,
                                                                                                "summary", "trace",
                                                                                                  langchian_inference[
                                                                                                    'trace_summary'],
                                                                                                "default",
                                                                                                "default")
        data_list = [value for value in pinecone_issue_data.values()]
        pinecone_interaction_provider.vectorize_data_and_push_to_pinecone_db(issue_id, incident_id, data_list)

    @staticmethod
    def get_time_stamp_from_datatime(date_time_str):
        if date_time_str is None:
            logger.error(log_tag, "dateTimeString is NONE")
            raise Exception("invalid date time string")
        try:
            timestamp_str = date_time_str.rstrip('Z')
            timestamp_dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
            timestamp_pg = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
            return timestamp_pg
        except Exception as e:
            logger.error(log_tag, f"Error formating datetime to timestamp datetime : {date_time_str} as error : {str(e)}")
            raise InferenceGenerationException(f"Error formating datetime to timestamp datetime : {date_time_str} as error : {str(e)}",
                                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                                             f"Error occurred during API call: {e}")