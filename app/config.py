import yaml
import os
import requests
import time
import contants


class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.secrets = None
        self._fetch_secrets_with_retry()
        self.config_data = self._load_config()

    def _load_config(self):
        try:
            with open(self.file_path, 'r') as file:
                config_data = yaml.safe_load(file)
                config_data.update(self.secrets)
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

    def fetch_secrets_from_server(self):
        try:
            response = requests.get(contants.OPERATOR_SECRETS_URL)
            response.raise_for_status()  # Raise an exception for non-200 status codes
            response_data = response.json()
            data = response_data['payload']
            print(data)
            return {
                "openai_key": data['openAI_key'],
                "pinecone_key": data['pinecone_key'],
                "pinecone_index": data['pinecone_index'],
                "pinecone_env": data['pinecone_env']
            }
            # return {
            #     "openai_key": "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",
            #     "pinecone_key": "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2",
            #     "pinecone_index": "zk-index-prod",
            #     "pinecone_env": "us-west4-gcp-free"
            # }
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
            raise Exception("Unable to fetch zk-llm Secrets from Server")

            # written this in future we can levarage

    def job(self):
        secrets = self.fetch_secrets_with_retry()
        if secrets:
            # Use secrets in your service or store them in the class instance
            self.secrets = secrets


configuration = Config("config/config.yaml")
