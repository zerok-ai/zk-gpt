from abc import ABC, abstractmethod

from app.clientServices import postgresClient
from app.clients import axon_client
from app.models.event_type import EventType
from app.internal.inference_adapter import inference_adapter
from app.internal.langchain_adapter import langchain_adapter
from app.internal.pinecone_adapter import pinecone_adapter
from app.models.request.user_qna_event_request import UserQnaEvent
from app.utils import context_cache
from app.utils import response_formatter

pinecone_interaction_provider = pinecone_adapter.PineconeAdapter()
lang_chain_inference_provider = langchain_adapter.LangchainAdapter()
inference_adapter_impl = inference_adapter.InferenceAdapter()
in_memory_context = context_cache.ContextCache(1000)
axon_svc_client = axon_client.AxonServiceClient()


class EventHandlingStrategy(ABC):
    @abstractmethod
    def handle_event(self, issue_id: str, incident_id: str, event_type: str, event: UserQnaEvent):
        pass


def get_issue_context(issue_id: str, incident_id: str):
    # check if context is present in memory or not
    cache_key = issue_id + '_' + incident_id
    context = in_memory_context.get_context(cache_key)
    if not context and context is not None and len(context) > 0:
        return context
    else:
        # fetch from DB
        context = postgresClient.fetch_issue_incident_context(issue_id, incident_id)
        # store in cache
        if context is not None and len(context) > 0:
            # in_memory_context.put_context(issue_id, context)
            return context
        else:
            return []


def upsert_issue_context(issue_id, incident_id, new_context):
    cache_key = issue_id + '_' + incident_id
    in_memory_context.upsert_context(cache_key, new_context)


class QNAEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id: str, incident_id: str, event_type: str, event: UserQnaEvent):
        if event_type == EventType.QNA.value:
            # Handle QNA event logic here
            # get context of the issue + final summary + user query fetch
            event_request = event.request
            query = event_request['query']

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

            # fetch context
            issue_context = get_issue_context(issue_id, incident_id)

            # fetch final summary
            issue_summary, incident_id_db = postgresClient.check_if_inference_already_present_for_issue(issue_id)

            # fetch pine cone documents
            pinecone_docs = pinecone_interaction_provider.get_similar_docs_for_given_query(query, issue_id)

            # fetch the inference
            # create input variable for langchain
            custom_data = {
                "query": query,
                "pinecone_similarity_docs": pinecone_docs,
                "issue_summary": issue_summary,
                "user_qna_context_data": issue_context,
                "trace_data": str(filtered_spans_map),
                "exception_data": str(exception_map),
                "request_response_payload": str(req_res_payload_map)
            }

            # get langchain inference
            langchian_inference = lang_chain_inference_provider.get_user_query_gpt_langchain_inference(issue_id,
                                                                                                       incident_id,
                                                                                                       custom_data)

            upsert_issue_context(issue_id, incident_id, issue_context)
            event_response = dict(type=EventType.QNA.value, response=str(langchian_inference['user_query_response']), query=query)

            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_type, query,
                                                          event_response)

            # update the context of the issue
            event_context = {
                "user_query": query,
                "gpt_response_for_query": langchian_inference['user_query_response']
            }
            issue_context.append(str(event_context))
            issue_context = issue_context[-30:]

            # upsert the context to DB
            postgresClient.upsert_issue_incident_context(issue_id, incident_id, issue_context)
            #  upsert the context to cache

            return {"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)}


class UserAdditionEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id: str, incident_id: str, event_type: str, event: UserQnaEvent):
        pass


class InferenceEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id: str, incident_id: str, event_type: str, event: UserQnaEvent):
        if event_type == EventType.INFERENCE.value:
            # check if inference already calculated for the issue and incident and send accordingly
            inference, issue_title = postgresClient.check_if_inference_already_present(issue_id, incident_id)
            # inference = None -> not present
            if inference is None:
                inference = inference_adapter_impl.generate_and_store_inference(issue_id,
                                                                                incident_id)
            # store the event conversation in DB
            inference_request = "Get likely cause for the issue : {}".format(issue_id)
            likely_cause = response_formatter.get_formatted_inference_response(issue_id, incident_id, inference)
            event_response = dict(type=EventType.INFERENCE.value, request=inference_request, response=likely_cause)
            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_type, inference_request,
                                                          event_response)

            # TODO: update the context of the issue

            return {"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)}


class TraceSwitchEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id: str, incident_id: str, event_type: str, event: UserQnaEvent):
        if event_type == EventType.CONTEXT_SWITCH.value:
            event_request = event.request
            # check if inference already calculated for the issue and incident and send accordingly
            old_incident = event_request['oldIncident']
            new_incident = event_request['newIncident']
            context_switch_request = "switch from incident id : {} to incident id : {}".format(old_incident,
                                                                                               new_incident)
            context_switch_response = "context switched from incident id : {} to incident id : {}".format(old_incident,
                                                                                                          new_incident)
            inference, issue_title = postgresClient.check_if_inference_already_present(issue_id, new_incident)
            # inference = None -> not present
            if inference is None:
                inference = inference_adapter_impl.generate_and_store_inference(issue_id,
                                                                                new_incident)

            event_response = dict(type=EventType.CONTEXT_SWITCH.value, request=context_switch_request, response=context_switch_response,
                                  oldIncident=old_incident, newIncident=new_incident)
            # store the event conversation in DB
            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_type, context_switch_request,
                                                          event_response)

            # TODO: update the context of the issue

            return {"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)}


# Create a strategy map
strategy_map = {
    EventType.QNA.value: QNAEventStrategy(),
    # EventType.USER_ADDITION.value: UserAdditionEventStrategy(),
    EventType.INFERENCE.value: InferenceEventStrategy(),
    EventType.CONTEXT_SWITCH.value: TraceSwitchEventStrategy()
}
