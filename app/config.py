import yaml
import os
import requests
import time
from app.utils import app_constants


class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.secrets = None
        self._fetch_secrets_with_retry()
        self.cluster_info_data = self._fetch_cluster_info()
        self.config_data = self._load_config()


    def _load_config(self):
        try:
            with open(self.file_path, 'r') as file:
                config_data = yaml.safe_load(file)
                config_data.update(self.secrets)
                config_data.update(self.cluster_info_data)
                return config_data
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    def get(self, key, default=None):
        # First, check if the key exists in the environment variables
        env_value = os.environ.get(key)
        if env_value:
            return env_value
        # If not found in environment variables, check if it exists in config data
        # If the key is not found in either config data or env, return the default value
        return self.config_data.get(key, default)

    def keys(self):
        return self.config_data.keys()

    def has_key(self, key):
        return key in self.config_data

    @staticmethod
    def fetch_secrets_from_server():
        try:
            # response = requests.get(app_constants.OPERATOR_SECRETS_URL)
            # response.raise_for_status()  # Raise an exception for non-200 status codes
            # response_data = response.json()
            # data = response_data['payload']
            # print(data)
            # return {
            #     "openai_key": data['openAI_key'],
            #     "pinecone_key": data['pinecone_key'],
            #     "pinecone_index": data['pinecone_index'],
            #     "pinecone_env": data['pinecone_env']
            # }
            return {
                "openai_key": "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",
                "pinecone_key": "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2",
                "pinecone_index": "zk-index-prod",
                "pinecone_env": "us-west4-gcp-free"
            }
        except requests.exceptions.RequestException as e:
            print(f"Secrets Fetch failed with error: {str(e)}")
            return None

    def _fetch_secrets_with_retry(self):
        max_retries = 5
        base_timeout = 1
        retries = 0
        while retries < max_retries:
            response = self.fetch_secrets_from_server()
            if response:
                self.secrets = response
                return
            # Exponential backoff, increase the retry timeout exponentially
            retries += 1
            sleep_duration = base_timeout * (2 ** retries)
            print(f"Retrying in {sleep_duration} seconds... for fetching the secrets")
            time.sleep(sleep_duration)
        if self.secrets is None:
            print("Unable to fetch zk-llm Secrets from Server")
            raise Exception("Unable to fetch zk-llm Secrets from Server")

    @staticmethod
    def _fetch_cluster_info():
        try:
            # response = requests.get(app_constants.OPERATOR_CLUSTER_ID_URL)
            # response.raise_for_status()  # Raise an exception for non-200 status codes
            # response_data = response.json()
            # data = response_data['payload']
            # if data is None or data['clusterId'] is None:
            #     print("cluster data is None")
            #     raise Exception("cluster Id is None")
            # return data
            return {
                "payload": {
                    "apiKey": "px-api-466ba2de-43d0-4d51-a678-005a5ecfb1d9",
                    "cloudAddr": "px.loadcloud01.getanton.com:443",
                    "clusterId": "56d95a4d-47e6-4acb-88cd-2588df9b6176"
                }
            }
        except Exception as e:
            raise ValueError(f"Error while fetching cluster id: {e}")


configuration = Config("config/config_local.yaml")
