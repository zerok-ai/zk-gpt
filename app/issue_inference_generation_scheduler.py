from apscheduler.schedulers.background import BackgroundScheduler
from clientServices import postgresClient
import client
import inference_engine
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


def generate_inference(issue_incident_dict):
    try:
        issue_id = issue_incident_dict["issue_id"]
        incident_id = issue_incident_dict["incident_id"]
        issue_data = issue_incident_dict["issue_data"]
        print(f"Generating inference for issue {issue_id} and incident {incident_id}")

        print(f"printing issue data for scheduler {issue_data}")
        inference_engine.generate_and_store_inference_for_scheduler(issue_id, incident_id, issue_data)
    except Exception as e:
        print(f"Error generating inference for issue {issue_incident_dict}: {str(e)}")


def task():
    print("Running issue scheduler")
    # fetch new issues from that timestamp
    # get last issue inferenced time stamp
    issues_data_list = client.getLatestIssuesData()

    if issues_data_list is None or len(issues_data_list) == 0:
        print("scheduler : No new issues found to infer")
        return

    print(issues_data_list)
    issues = [issue['issue_hash'] for issue in issues_data_list]
    issue_data_dict = {}
    for issue in issues_data_list:
        issue_id = issue["issue_hash"]
        issue_data_dict[issue_id] = issue

    issue_dict = {}
    # Iterate through the list and create the dictionary
    incidents = {}
    for item in issues_data_list:
        issue_hash = item["issue_hash"]
        issue_dict[issue_hash] = item
        incidents[issue_hash] = item["incidents"]

    if len(issues) == 0 or issues is None:
        print("scheduler : No new issues found to infer")
        return

    # check if the issue is inferred and  present in the DB
    issues_already_inferred = postgresClient.get_issues_inferred_already_in_db(issues)

    # update last seen for already inferred issues
    issue_last_seen_dict = {}
    issue_last_seen_dict_list = []

    for issueId in issues_already_inferred:
        timestamp_str = issue_data_dict[issueId]["last_seen"]
        timestamp_dt = datetime.fromisoformat(timestamp_str)
        timestamp_pg = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        issue_last_seen_dict[issueId] = timestamp_pg
        issue_last_seen_dict_list.append({"issue_id": issueId, "last_seen": timestamp_pg})
    postgresClient.update_last_seen_for_issue_list(issue_last_seen_dict_list)

    new_issues_to_infer = list(set(issues) - set(issues_already_inferred))
    if len(new_issues_to_infer) == 0:
        print("scheduler : No new issues found to infer")
        return

    new_issue_incident_dict = []
    for item in new_issues_to_infer:
        if len(incidents[item]) > 0:
            new_issue_incident_dict.append({"issue_id": item, "incident_id": incidents[item][0], "issue_data": issue_data_dict[item]})

    print(f"Found {new_issue_incident_dict} new issues to infer: ")
    with ThreadPoolExecutor() as executor:
        executor.map(generate_inference, new_issue_incident_dict)


issue_scheduler = BackgroundScheduler()
issue_scheduler.add_job(task, 'interval', minutes=3)
