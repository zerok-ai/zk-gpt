from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler

from clientServices import postgresClient, wsp_client


def publish_issue_inference_slack_report(issue_incident_dict):
    issue_id = issue_incident_dict["issue_id"]
    incident_id = issue_incident_dict["incident_id"]
    clear_reporting_timestamp = issue_incident_dict["clear_reporting_timestamp"]

    print("publish_issue_inference_slack_report"+ str(issue_incident_dict))

    try:
        # fetch inference
        inference, issue_title, issue_last_seen = postgresClient.check_if_inference_already_present_reporting_scheduler(issue_id, incident_id)
        if inference is None:
            return
        if issue_last_seen < clear_reporting_timestamp:
            return

        wsp_client.publish_inference_to_slack(issue_id, incident_id,inference, issue_title)
        # update the status of the slack reporting
        postgresClient.update_slack_reporting_status(issue_id, incident_id,True)
    except Exception as e:
        print(f"Error while reporting inference for issue {issue_incident_dict}: {str(e)}")
        postgresClient.update_slack_reporting_status(issue_id, incident_id, False)


def reporting_task():
    print("Running slack report scheduler")
    # fetch new issues to be reported
    issues_incident_list = postgresClient.fetch_issues_to_be_reported_to_slack()

    if len(issues_incident_list) == 0:
        print("reporting scheduler : No new issues found to report")
        return
    print(f"Found {issues_incident_list} new issues to report")
    with ThreadPoolExecutor() as executor:
        executor.map(publish_issue_inference_slack_report, issues_incident_list)


slack_reporting_scheduler = BackgroundScheduler()
slack_reporting_scheduler.add_job(reporting_task, 'interval', minutes=1)
