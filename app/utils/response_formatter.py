from app.models.response.fetch_inference_respone import InferenceSummaryAnomaly
from app.utils import zk_logger

log_tag = "response_formatter"
logger = zk_logger.logger


def get_formatted_inference_response(issue_id: str, incident_id: str, inference: str) -> InferenceSummaryAnomaly:
    inference_summary_anomaly = {
        "summary": None,
        "anomalies": None,
        "data": inference
    }
    try:
        split_response = inference.split("Anomalies:")
        if len(split_response) > 1:
            # If "Anomalies" keyword is present, store the summary and anomalies
            inference_summary_anomaly["summary"] = split_response[0]
            inference_summary_anomaly["anomalies"] = split_response[1].strip()
        else:
            # If "Anomalies" keyword is not present, store the entire response as summary
            inference_summary_anomaly["summary"] = inference.strip()

        return InferenceSummaryAnomaly(data=inference, summary=inference_summary_anomaly["summary"], anomalies=inference_summary_anomaly["anomalies"])
    except Exception as e:
        logger.error(log_tag, "exception occurred like parsing the langchain response for issue:{} incident:{}".format(issue_id,
                                                                                                       incident_id))
        return InferenceSummaryAnomaly(data=inference, summary=None, anomalies=None)
