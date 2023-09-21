from apscheduler.schedulers.background import BackgroundScheduler
from clientServices import postgresClient
import client
import inference_engine
from concurrent.futures import ThreadPoolExecutor


def generate_inference(issue, issue_dict):
    try:
        incident_id = issue_dict[issue]['incidents'][0]
        inference_engine.generate_and_store_inference(issue, incident_id)
    except Exception as e:
        print(f"Error generating inference for issue {issue}: {str(e)}")


def task():
    print("Running issue scheduler")
    # fetch new issues from that timestamp
    # get last issue inferenced time stamp
    issues_data_list = client.getLatestIssuesData()
    issues = [issue['issue_hash'] for issue in issues_data_list]
    issue_dict = {}

    # Iterate through the list and create the dictionary
    for item in issues_data_list:
        issue_hash = item["issue_hash"]
        issue_dict[issue_hash] = item

    # check if the issue is inferenced present in the DB
    new_issues_list = postgresClient.get_issues_zero_count_inference_in_db(issues)

    with ThreadPoolExecutor() as executor:
        executor.map(generate_inference, new_issues_list, issue_dict)


issue_scheduler = BackgroundScheduler()
issue_scheduler.add_job(task, 'interval', minutes=15)
