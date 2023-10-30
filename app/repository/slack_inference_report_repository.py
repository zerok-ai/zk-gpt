from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.db import SlackInferenceReportDB
from app.models.models import SlackInferenceReport
import database
from datetime import datetime
from app.utils import zk_logger

log_tag = "slack_inference_report_repository"
logger = zk_logger.logger


class SlackInferenceReportRepository:
    def __init__(self, db: Session):
        self.db = database.db

    def create_inference(self, item: SlackInferenceReport):
        try:
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception as e:
            logger.error(log_tag, f"Error while inserting slack inference report item: {str(item)} with "
                                  f"error: {str(e)}")
            raise Exception(f"Error while inserting slack inference report item: {str(item)} with "
                            f"error: {str(e)}")

    def get_unreported_issues(self):
        try:
            issue_incident_dict = self.db.query(
                SlackInferenceReport.issue_id,
                SlackInferenceReport.incident_id,
                SlackInferenceReport.clear_reporting_timestamp
            ).filter(
                SlackInferenceReport.reporting_status == False
            ).all()

            issue_incident_list = [{"issue_id": issue_id, "incident_id": incident_id,
                                    "clear_reporting_timestamp": clear_reporting_timestamp}
                                   for issue_id, incident_id, clear_reporting_timestamp in issue_incident_dict]

            return issue_incident_list
        except Exception as error:
            logger.error(log_tag, "Error fetching unreported issues from PostgreSQL:", error)
            return []

    def update_reporting_status(self, issue_id, incident_id, status):
        try:
            self.db.query(SlackInferenceReport).filter(
                SlackInferenceReport.issue_id == issue_id,
                SlackInferenceReport.incident_id == incident_id
            ).update({
                SlackInferenceReport.reporting_status: status
            })
            self.db.commit()
            logger.info(log_tag, f"Reporting Status updated successfully for issue: {issue_id} as status: {status}")
        except Exception as e:
            logger.error(log_tag, f"Error updating status in PostgreSQL: {str(e)}")
            self.db.rollback()

    def clear_slack_reporting_for_demo(self):
        try:
            self.db.query(SlackInferenceReportDB).update({
                SlackInferenceReportDB.reporting_status: False,
                SlackInferenceReportDB.clear_reporting_timestamp: datetime.now()
            })
            self.db.commit()
            logger.info(log_tag, "Status updated successfully for all rows.")
        except Exception as e:
            logger.error(log_tag, f"Error updating status in PostgreSQL: {str(e)}")
            raise Exception(f"Error while creating reporting status for demo: {str(e)}")

    def check_if_reporting_already_present_for_issue(self, issue_id):
        try:
            result = self.db.query(SlackInferenceReportDB.issue_id).filter({
                SlackInferenceReportDB.issue_id == issue_id
            }).order_by(SlackInferenceReportDB.created_at.desc()).limit(1).first()

            if result is not None:
                issue_id = result
                return issue_id
            else:
                return None
        except Exception as e:
            logger.error(log_tag, f"Error while fetching if reporting is already present for issue: {issue_id} with "
                                  f"error: {str(e)}")
            raise Exception(f"Error while fetching if reporting is already present for issue: {issue_id} with "
                            f"error: {str(e)}")
