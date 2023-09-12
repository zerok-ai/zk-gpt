import json

import redis
import requests

import config

axon_host = config.configuration.get("axon_host", "localhost:8080")
redis_host = config.configuration.get("redis_host", "localhost")
redis_db = 6


def getIssueSummary(issue_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        issueSummary = data['payload']['issue']
        return issueSummary
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getScenario(scenario_id):
    try:
        # Connect to Redis
        r = redis.StrictRedis(host=redis_host, port=6379, db=redis_db)

        # Read the JSON object from the specified key
        json_data = r.get(scenario_id)

        # If the key is not found or the value is None, return None
        if json_data is None:
            return None

        # Decode the JSON data
        scenario = json.loads(json_data)

        return scenario
    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
    except Exception as e:
        print(f"Error reading JSON from Redis: {e}")
        return None


def getScenarioStats(scenario_id):
    url = f"http://{axon_host}/v1/c/axon/scenario"
    params = {"scenario_id_list": scenario_id, "st": "-12h"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        scenarioDetail = data['payload']['scenarios']
        return scenarioDetail
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getSpansMap(issue_id, incident_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident/{incident_id}"
    params = {"limit": 10, "offset": 0}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spansMap = data['payload']['spans']
        return spansMap
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")


def getIssueIncidents(issue_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident"
    params = {"limit": 50, "offset": 0}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status  # Raise an HTTPError exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        incidents = data['payload']['trace_id_list']
        return incidents
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching incident Ids for a given issue : {e}")


def getSpanRawdata(issue_id, incident_id, span_id):
    url = f"http://{axon_host}/v1/c/axon/issue/{issue_id}/incident/{incident_id}/span/{span_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx and 5xx status codes)
        data = response.json()
        spanRawdata = data['payload']['span_raw_data_details'][span_id]
        return spanRawdata
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API call: {e}")
