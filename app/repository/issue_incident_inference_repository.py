from sqlalchemy.orm import Session
from app.models.db import IssueIncidentInferenceDB
from app.models.models import IssueIncidentInference
from sqlalchemy import func
from app.utils import zk_logger
import database
import pickle

log_tag = "issue_incident_inference_repository"
logger = zk_logger.logger

class IssueIncidentInferenceRepository:
    def __init__(self, db: Session):
        self.db = database.db

    def create_inference(self, item: IssueIncidentInference):
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def find_by_issue_id_and_incident_id(self, issue_id: str, incident_id: str):
        return self.db.query(IssueIncidentInferenceDB).filter(
            IssueIncidentInferenceDB.issue_id == issue_id,
            IssueIncidentInferenceDB.incident_id == incident_id
        ).first()

    def find_inference_title_last_seen(self, issue_id, incident_id):
        result = self.db.query(
            IssueIncidentInferenceDB.inference,
            IssueIncidentInferenceDB.issue_title,
            IssueIncidentInferenceDB.issue_last_seen
        ).filter(
            IssueIncidentInferenceDB.issue_id == issue_id,
            IssueIncidentInferenceDB.incident_id == incident_id
        ).first()

        if result is not None:
            inference, issue_title, issue_last_seen = result
            return inference, issue_title, issue_last_seen
        else:
            return None, None, None

    def find_latest_inference_for_issue(self, issue_id):
        result = self.db.query(
            IssueIncidentInferenceDB.inference,
            IssueIncidentInferenceDB.incident_id
        ).filter(
            IssueIncidentInferenceDB.issue_id == issue_id
        ).order_by(IssueIncidentInferenceDB.created_at.desc()).limit(1).first()

        if result is not None:
            inference, incident_id = result
            return inference, incident_id
        else:
            return None, None

    def count_rows_by_issue_ids(self, issue_ids):
        result = self.db.query(
            IssueIncidentInferenceDB.issue_id,
            func.count().label('row_count')
        ).filter(
            IssueIncidentInferenceDB.issue_id.in_(issue_ids)
        ).group_by(
            IssueIncidentInferenceDB.issue_id
        ).all()

        return result

    def update_issue_last_seen(self, issue_id, new_issue_last_seen):
        try:
            self.db.query(IssueIncidentInferenceDB).filter(
                IssueIncidentInferenceDB.issue_id == issue_id
            ).update({
                IssueIncidentInferenceDB.issue_last_seen: new_issue_last_seen
            })
            self.db.commit()
        except Exception as e:
            self.db.rollback()

    def get_issue_last_seen(self, issue_id, incident_id):
        result = self.db.query(
            IssueIncidentInferenceDB.issue_last_seen
        ).filter(
            IssueIncidentInferenceDB.issue_id == issue_id,
            IssueIncidentInferenceDB.incident_id == incident_id
        ).first()

        if result is not None:
            issue_last_seen = result[0]
            return issue_last_seen
        else:
            return None

    def get_last_seen_for_issues(self, issues_incident_list):
        output_dict_list = []

        for issue_incident_item in issues_incident_list:
            issue_id = issue_incident_item["issue_id"]
            incident_id = issue_incident_item["incident_id"]

            # Use the repository method to fetch issue_last_seen
            issue_last_seen = self.get_issue_last_seen(issue_id, incident_id)

            if issue_last_seen is not None:
                # Update the input dictionary with issue_last_seen
                issue_incident_item["issue_last_seen"] = issue_last_seen
                output_dict_list.append(issue_incident_item)
                logger.info(log_tag, f"Fetched issue_last_seen and updated data_dict: {issue_incident_item}")
            else:
                logger.error(log_tag, f"No matching record found for Issue ID: {issue_id}, Incident ID: {incident_id}")


