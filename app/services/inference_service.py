from app.clientServices import postgresClient
from app.dao import dataDao
from app.internal.inference_adapter import inference_adapter
from app.internal.pinecone_adapter import pinecone_adapter
from app.internal.user_events_adapter import event_type_handler
from app.models.response.fetch_inference_respone import FetchInferenceResponse
from app.utils import response_formatter, zk_logger

inference_adapter = inference_adapter.InferenceAdapter()
pinecone_interaction_provider = pinecone_adapter.PineconeAdapter()
log_tag = "inference_service"
logger = zk_logger.logger


class InferenceService:

    def get_incident_likely_cause(self, issue_id: str, incident_id: str) -> FetchInferenceResponse:
        if issue_id is None:
            raise Exception("issue_id is None")

        # regenerateRca = false check if rca already calculated for the issue send accordingly
        inference_db, incident_id_db = postgresClient.check_if_inference_already_present_for_issue(issue_id)

        if inference_db is not None and incident_id_db is not None:
            formatted_inference = response_formatter.get_formatted_inference_response(issue_id, incident_id_db, inference_db)
            return FetchInferenceResponse(issue_id=issue_id, incident_id=incident_id_db,inference=formatted_inference)

        if incident_id is None or incident_id == "":
            # fetch latest incident_id for the issue
            incident_id = dataDao.get_latest_incident_id(issue_id)

        if incident_id is None:
            raise Exception("Given issue : {} doesn't have any trace ".format(issue_id))

        # # regenerateRca = false check if rca already calculated for the issue and incident and send accordingly
        # inference = postgresClient.check_if_inference_already_present(issue_id, incident_id)
        # # inference = None not present
        # if inference is None:
        inference = inference_adapter.generate_and_store_inference(issue_id,
                                                                   incident_id)  # check update or insert logic also

        formatted_inference = response_formatter.get_formatted_inference_response(issue_id, incident_id,
                                                                                  inference)
        fetch_inference_response = FetchInferenceResponse(issue_id=issue_id, incident_id=incident_id,
                                                          inference=formatted_inference)
        return fetch_inference_response

    def get_all_issue_inferences(self, issue_id, limit, offset):
        logger.info(log_tag, "Fetching all the inferences for the given issue id :{issue_id}")
        user_inferences = postgresClient.get_all_user_issue_inferences(issue_id, limit, offset)
        return user_inferences

    def update_user_issue_observation_feedback(self, requestId, feedback, score):
        logger.info(log_tag, "Updating the User Feedback for the infernce with requestId : {requsetId}")
        postgresClient.update_user_inference_feedback(requestId, feedback, score)

    def get_issue_observation_with_params(self, issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel,
                                          requestId):
        if not postgresClient.check_issue_presence_in_db(issue_id):
            pinecone_interaction_provider.vectorize_issue_and_pushtu_pinecone_db(issue_id)
        response = pinecone_interaction_provider.get_gpt_inferences_for_query_custom_data(issue_id, query, temperature,
                                                                                          topK)
        postgresClient.insert_user_issue_inference(issue_id, query, temperature, topK, vectorEmbeddingModel, gptModel,
                                                   requestId, response)
        return response

    def get_issue_observation(self, issue_id, query):
        if not postgresClient.check_issue_presence_in_db(issue_id):
            pinecone_interaction_provider.vectorize_issue_and_pushtu_pinecone_db(issue_id)

        return pinecone_interaction_provider.get_gpt_inferences_for_query_custom_data(issue_id, query, 0.3, 30)

    def process_incident_event_and_get_event_response(self, issue_id, incident_id, event_type, event):
        # understand the event type
        # if event type is :
        # "QNA" then push fetch the context and fetch the pinecone vectors and also eventRequest as prompt to GPT
        # "INFERENCE" then fetch the langchain inference
        strategy_map = event_type_handler.strategy_map
        if event_type in strategy_map:
            strategy = strategy_map[event_type]
            return strategy.handle_event(issue_id, incident_id, event_type, event)
        else:
            raise Exception("Event type : {} is not supported".format(event_type))
