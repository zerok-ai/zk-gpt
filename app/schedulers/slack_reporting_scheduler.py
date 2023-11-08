from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler

from app.clientServices import postgresClient
from app.clients import wsp_client
from app.utils import zk_logger

wsp_svc_client = wsp_client.WSPServiceClient()
log_tag = "slack_reporting_scheduler"
logger = zk_logger.logger


def publish_issue_inference_slack_report(issue_incident_dict):
    issue_id = issue_incident_dict["issue_id"]
    incident_id = issue_incident_dict["incident_id"]
    clear_reporting_timestamp = issue_incident_dict["clear_reporting_timestamp"]

    logger.info(log_tag, "publish_issue_inference_slack_report" + str(issue_incident_dict))

    try:
        # fetch inference
        inference, issue_title, issue_last_seen, scenario_id = postgresClient.check_if_inference_already_present_reporting_scheduler(issue_id, incident_id)
        if inference is None:
            return
        if issue_last_seen < clear_reporting_timestamp:
            return

        wsp_svc_client.publish_inference_to_slack(issue_id, incident_id,inference, issue_title, scenario_id)
        # update the status of the slack reporting
        postgresClient.update_slack_reporting_status(issue_id, incident_id,True)
    except Exception as e:
        logger.error(log_tag, f"Error while reporting inference for issue {issue_incident_dict}: {str(e)}")
        postgresClient.update_slack_reporting_status(issue_id, incident_id, False)


def slack_reporting_scheduler_task():
    logger.info(log_tag, "Running slack report scheduler")
    # fetch new issues to be reported
    issues_incident_list = postgresClient.fetch_issues_to_be_reported_to_slack()

    if len(issues_incident_list) == 0:
        logger.info(log_tag, "reporting scheduler : No new issues found to report")
        return
    logger.info(log_tag, f"Found {issues_incident_list} new issues to report")
    with ThreadPoolExecutor() as executor:
        executor.map(publish_issue_inference_slack_report, issues_incident_list)


slack_reporting_scheduler = BackgroundScheduler()
slack_reporting_scheduler.add_job(slack_reporting_scheduler_task, 'interval', minutes=3, max_instances=2)
