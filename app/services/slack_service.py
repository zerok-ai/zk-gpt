from app.clientServices import postgresClient
from app.utils import zk_logger

log_tag = "slack_service"
logger = zk_logger.logger


class SlackService:
    def store_inference_for_reporting(self, issue_id: str, incident_id: str, issue_last_seen: str):
        # check if it is present in DB
        logger.info(log_tag, f"Storing in Reporting DB for IssueId: {issue_id} and IncidentId:{incident_id}")
        issue_id_db = postgresClient.check_if_reporting_already_present_for_issue(issue_id)
        if issue_id_db is not None:
            logger.info(log_tag, "inference report already exists for issueId: {}",issue_id)
            return
        # store in DB
        postgresClient.insert_issue_inference_to_slack_reporting_db(issue_id, incident_id, issue_last_seen)