import requests
import config

host = config.configuration.get("host", "localhost:8080")


def getSpansMap(issue_id, incident_id):
    url = f"http://{host}/v1/c/issue/{issue_id}/incident/{incident_id}"
    params = {"limit": 10, "offset": 0}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spansMap = data['payload']['spans']
        return spansMap
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getSpanRawdata(issue_id, incident_id, span_id):
    url = f"http://{host}/v1/c/issue/{issue_id}/incident/{incident_id}/span/{span_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spanRawdata = data['payload']['span_raw_data_details'][span_id]
        return spanRawdata
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")
