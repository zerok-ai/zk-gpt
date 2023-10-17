from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.background import BackgroundScheduler

from app.clientServices import postgresClient, wsp_client


def publish_issue_inference_slack_report(issue_incident_dict):
    issue_id = issue_incident_dict["issue_id"]
    incident_id = issue_incident_dict["incident_id"]
    try:
        # fetch inference
        inference, issue_title = postgresClient.check_if_inference_already_present(issue_id, incident_id)
        if inference is None:
            return

        wsp_client.publish_inference_to_slack(issue_id, incident_id,inference, issue_title)
        # update the status of the slack reporting
        postgresClient.update_slack_reporting_status(issue_id, incident_id,True)
    except Exception as e:
        print(f"Error while reporting inference for issue {issue_incident_dict}: {str(e)}")
        postgresClient.update_slack_reporting_status(issue_id, incident_id, False)


def task():
    print("Running slack report scheduler")
    # fetch new issues to be reported
    issues_incident_list = postgresClient.fetch_issues_to_be_reported_to_slack()

    if len(issues_incident_list) == 0:
        print("report scheduler : No new issues found to report")
        return
    print(f"Found {issues_incident_list} new issues to report")
    with ThreadPoolExecutor() as executor:
        executor.map(publish_issue_inference_slack_report, issues_incident_list)


issue_scheduler = BackgroundScheduler()
issue_scheduler.add_job(task, 'interval', minutes=3)
