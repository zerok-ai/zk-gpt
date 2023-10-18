from clientServices import postgresClient


def store_inference_for_reporting(issue_id, incident_id):
    # check if it is present in DB
    print(f"Storing in reposrting DB for issueId: {issue_id} and incidentId:{incident_id}")
    issue_id_db = postgresClient.check_if_reporting_already_present_for_issue(issue_id)
    if issue_id_db is not None:
        print("inference report already exists for issueId: {}",issue_id)
        return
    # store in DB
    postgresClient.insert_issue_inference_to_slack_reporting_db(issue_id, incident_id)

