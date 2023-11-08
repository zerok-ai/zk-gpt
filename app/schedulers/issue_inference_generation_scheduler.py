from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict

from apscheduler.schedulers.background import BackgroundScheduler

from app.clientServices import postgresClient
from app.clients import axon_client
from app.internal.inference_adapter import inference_adapter
from app.utils import zk_logger

axon_svc_client = axon_client.AxonServiceClient()
inference_adapter_impl = inference_adapter.InferenceAdapter()
log_tag = "issue_inference_generation_scheduler"
logger = zk_logger.logger


def generate_inference(issue_incident_dict):
    try:
        issue_id = issue_incident_dict["issue_id"]
        incident_id = issue_incident_dict["incident_id"]
        issue_data: Dict[str, str] = issue_incident_dict["issue_data"]
        logger.info(log_tag, f"Generating Inference for Issue {issue_id} and Incident {incident_id}")
        logger.info(log_tag, f"printing issue data for scheduler {issue_data}")
        inference_adapter_impl.generate_inference_for_scheduler(issue_id=issue_id, incident_id=incident_id, issue_data=issue_data)
    except Exception as e:
        logger.error(log_tag, f"Error generating inference for issue {issue_incident_dict}: {str(e)}")


def get_time_stamp_from_datatime(date_time_str):
    if date_time_str is None:
        logger.info(log_tag, "dateTimeString is NONE")
        raise Exception("invalid date time string")
    try:
        timestamp_str = date_time_str.rstrip('Z')
        timestamp_dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
        timestamp_pg = timestamp_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        return timestamp_pg
    except Exception as e:
        logger.error(log_tag, f"Error formating datetime to timestamp datetime : {date_time_str} as error : {str(e)}")
        raise Exception(f"Error formating datetime to timestamp datetime : {date_time_str} as error : {str(e)}")


def issue_inference_scheduler_task():
    logger.info(log_tag, "Running Issue Inference Scheduler")
    # fetch new issues from that timestamp
    # get last issue inferenced time stamp
    issues_data_list = axon_svc_client.get_latest_issues_data()

    if issues_data_list is None or len(issues_data_list) == 0:
        logger.info(log_tag, "issue scheduler : No new issues found to infer")
        return

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
        logger.info(log_tag, "issue scheduler : No new issues found to infer")
        return

    # check if the issue is inferred and  present in the DB
    issues_already_inferred = postgresClient.get_issues_inferred_already_in_db(issues)
    # update last seen for already inferred issues
    issue_last_seen_dict = {}
    issue_last_seen_dict_list = []

    for issueId in issues_already_inferred:
        timestamp_str = issue_data_dict[issueId]["last_seen"]
        timestamp_pg = get_time_stamp_from_datatime(timestamp_str)
        issue_last_seen_dict[issueId] = timestamp_pg
        issue_last_seen_dict_list.append({"issue_id": issueId, "last_seen": timestamp_pg})
    postgresClient.update_last_seen_for_issue_list(issue_last_seen_dict_list)
    new_issues_to_infer = list(set(issues) - set(issues_already_inferred))
    if len(new_issues_to_infer) == 0:
        logger.info(log_tag, "issue scheduler : No new issues found to infer")
        return

    new_issue_incident_dict = []
    for item in new_issues_to_infer:
        if len(incidents[item]) > 0:
            new_issue_incident_dict.append(
                {"issue_id": item, "incident_id": incidents[item][0], "issue_data": issue_data_dict[item]})

    logger.info(log_tag, f"Found {new_issue_incident_dict} new issues to infer: ")
    with ThreadPoolExecutor() as executor:
        executor.map(generate_inference, new_issue_incident_dict)


issue_scheduler = BackgroundScheduler()
issue_scheduler.add_job(issue_inference_scheduler_task, 'interval', minutes=1, max_instances=3)
