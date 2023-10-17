from apscheduler.schedulers.background import BackgroundScheduler
from app.clientServices import postgresClient
from app import client
from app import inference_engine
from concurrent.futures import ThreadPoolExecutor


def generate_inference(issue_incident_dict):
    try:
        issue_id = issue_incident_dict["issue_id"]
        incident_id = issue_incident_dict["incident_id"]
        print(f"Generating inference for issue {issue_id} and incident {incident_id}")
        inference_engine.generate_and_store_inference(issue_id, incident_id)
    except Exception as e:
        print(f"Error generating inference for issue {issue_incident_dict}: {str(e)}")


def task():
    print("Running issue scheduler")
    # fetch new issues from that timestamp
    # get last issue inferenced time stamp
    issues_data_list = client.getLatestIssuesData()

    issues = [issue['issue_hash'] for issue in issues_data_list]
    issue_dict = {}

    # Iterate through the list and create the dictionary
    incidents = {}
    for item in issues_data_list:
        issue_hash = item["issue_hash"]
        issue_dict[issue_hash] = item
        incidents[issue_hash] = item["incidents"]

    # check if the issue is inferenced present in the DB
    issues_already_inferred = postgresClient.get_issues_inferred_already_in_db(issues)

    new_issues_to_infer = list(set(issues) - set(issues_already_inferred))
    if len(new_issues_to_infer) == 0:
        print("scheduler : No new issues found to infer")
        return

    new_issue_incident_dict = []
    for item in new_issues_to_infer:
        if len(incidents[item]) > 0:
            new_issue_incident_dict.append({"issue_id": item, "incident_id": incidents[item][0]})

    print(f"Found {new_issue_incident_dict} new issues to infer")
    with ThreadPoolExecutor() as executor:
        executor.map(generate_inference, new_issue_incident_dict)


issue_scheduler = BackgroundScheduler()
issue_scheduler.add_job(task, 'interval', minutes=15)
