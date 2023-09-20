from abc import ABC, abstractmethod

from enums.event_type import EventType
from flask import jsonify


import pineconeInteraction
import gptLangchianInference
import inference_engine
from clientServices import postgresClient
import context_cache
import response_formatter


pineconeInteractionProvider = pineconeInteraction.PineconeInteraction()
langChainInferenceProvider = gptLangchianInference.LangChainInference()
in_memory_context = context_cache.ContextCache(1000)


class EventHandlingStrategy(ABC):
    @abstractmethod
    def handle_event(self, issue_id, incident_id, event_type, event):
        pass


def get_issue_context(issue_id, incident_id):
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
    def handle_event(self, issue_id, incident_id, event_type, event):
        if event_type == EventType.QNA.value:
            # Handle QNA event logic here
            # get context of the issue + final summary + user query fetch
            event_request = event['request']
            query = event_request['query']
            # fetch context
            issue_context = get_issue_context(issue_id, incident_id)

            # fetch final summary
            issue_summary, incident_id_db = postgresClient.check_if_inference_already_present_for_issue(issue_id)

            # fetch pine cone documents
            pinecone_docs = pineconeInteractionProvider.get_similar_docs_for_given_query(query, issue_id)

            # fetch the inference
            # create input variable for langchain
            custom_data = {
                "query": query,
                "pinecone_similarity_docs": pinecone_docs,
                "issue_summary": issue_summary,
                "user_qna_context_data": issue_context
            }

            # get langchain inference
            langchian_inference = langChainInferenceProvider.get_user_query_gpt_langchain_inference(issue_id,
                                                                                                    incident_id,
                                                                                                    custom_data)

            upsert_issue_context(issue_id, incident_id, issue_context)
            event_response = dict(type="QNA", response=langchian_inference['user_query_response'], query=query)

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

            return jsonify({"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)})



class UserAdditionEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event):
        pass


class InferenceEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event):
        if event_type == EventType.INFERENCE.value:
            event_request = event['request']
            # check if inference already calculated for the issue and incident and send accordingly
            inference = postgresClient.check_if_inference_already_present(issue_id, incident_id)
            # inference = None -> not present
            if inference is None:
                inference = inference_engine.generate_and_store_inference(issue_id,
                                                                          incident_id)
            # store the event conversation in DB
            inference_request = "Get likely cause for the issue : {}".format(issue_id)
            likely_cause = response_formatter.get_formatted_inference_response(issue_id, incident_id, inference)
            event_response = dict(type="INFERENCE", inference=likely_cause)
            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_type, inference_request, event_response)

            # TODO: update the context of the issue

            return jsonify({"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)})


class TraceSwitchEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event):
        if event_type == EventType.CONTEXT_SWITCH.value:
            event_request = event['request']
            # check if inference already calculated for the issue and incident and send accordingly
            old_incident = event_request['oldIncident']
            new_incident = event_request['newIncident']
            context_switch_request = "context switched from incident id : {} to incident id : {}".format(old_incident,
                                                                                                         new_incident)
            inference = postgresClient.check_if_inference_already_present(issue_id, new_incident)
            # inference = None -> not present
            if inference is None:
                inference = inference_engine.generate_and_store_inference(issue_id,
                                                                          new_incident)

            event_response = dict(oldIncident=old_incident, newIncident=new_incident)
            # store the event conversation in DB
            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_type, context_switch_request, event_response)

            # TODO: update the context of the issue

            return jsonify({"payload": dict(issueId=issue_id, incidentId=incident_id, event=event_response)})


# Create a strategy map
strategy_map = {
    EventType.QNA.value: QNAEventStrategy(),
    # EventType.USER_ADDITION.value: UserAdditionEventStrategy(),
    EventType.INFERENCE.value: InferenceEventStrategy(),
    EventType.CONTEXT_SWITCH.value: TraceSwitchEventStrategy()
}
