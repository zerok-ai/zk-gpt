from abc import ABC, abstractmethod

from enums.event_type import EventType

import inference_engine
from clientServices import postgresClient
import response_formatter


class EventHandlingStrategy(ABC):
    @abstractmethod
    def handle_event(self, issue_id, incident_id, event_type, event_request):
        pass


class QNAEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event_request):
        if event_type == EventType.QNA:
            # Handle QNA event logic here
            # get context of the issue + final summary + user query fetch

            pass


class UserAdditionEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event_request):
        pass


class InferenceEventStrategy(EventHandlingStrategy):
    def handle_event(self, issue_id, incident_id, event_type, event_request):
        if event_type == EventType.INFERENCE:
            # Handle USER_ADDITION event logic here
            # check if inference is already done for issue_id : incident_id
            # check if inference already calculated for the issue and incident and send accordingly
            inference = postgresClient.check_if_inference_already_present(issue_id, incident_id)
            # inference = None not present
            if inference is None:
                inference = inference_engine.generate_and_store_inference(issue_id,
                                                                          incident_id)
            # store the event conversation in DB
            postgresClient.insert_user_conversation_event(issue_id, incident_id, event_request, event_type, inference)

            # TODO: update the context of the issue

            return response_formatter.get_formatted_inference_response(issue_id, incident_id, inference)


# Create a strategy map
strategy_map = {
    EventType.QNA: QNAEventStrategy(),
    EventType.USER_ADDITION: UserAdditionEventStrategy(),
    EventType.INFERENCE: InferenceEventStrategy(),
}
