from app.clientServices import postgresClient
class UserEventsService:
    def get_user_conversation_events(self, issue_id, limit, offset):
        total_count, user_conserve_events_response = postgresClient.get_user_conversation_events(issue_id, limit,
                                                                                                 offset)
        return total_count, user_conserve_events_response
