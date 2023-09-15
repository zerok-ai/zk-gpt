def get_formatted_inference_response(issue_id, incident_id, inference):
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
        return issue_id, incident_id, inference_summary_anomaly
    except Exception as e:
        print("exception occurred like parsing the langchain response for issue:{} incident:{}".format(issue_id,
                                                                                                       incident_id))
        return issue_id, incident_id, inference_summary_anomaly
