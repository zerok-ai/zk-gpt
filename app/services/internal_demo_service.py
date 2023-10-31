from app.clientServices import postgresClient


class InternalDemoService:

    @staticmethod
    def clear_slack_reporting(self):
        postgresClient.clear_slack_reporting_for_demo()

    @staticmethod
    def clear_all_issue_data_for_demo(self):
        postgresClient.clear_all_issue_data_for_demo()
