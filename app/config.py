import yaml
import os
import requests
import time

class Config:
    def __init__(self, file_path):
        self.file_path = file_path
        self.secrets = None
        self._fetch_secrets_with_retry()
        self.config_data = self._load_config()
        
    def _load_config(self):
        try:
            with open(self.file_path, 'r') as file:
                config_dict = yaml.safe_load(file)
                config_dict.update(self.secrets['payload'])
                return config_dict
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
            response = requests.get("http://<operatorUrl:port>/i/configuration?svc=zk-gpt")
            response.raise_for_status()  # Raise an exception for non-200 status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Secrets Fetch failed with error: {str(e)}")
            return None

    def _fetch_secrets_with_retry(self):
        max_retries=5
        base_timeout=1
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


    def job(self):
        secrets = self.fetch_secrets_with_retry()
        if secrets:
            # Use secrets in your service or store them in the class instance
            self.secrets = secrets

configuration = Config("config/config.yaml")