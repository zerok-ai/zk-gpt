import datetime
import random

from langchain.callbacks import LangChainTracer
from langsmith import Client

from app import config
from app.utils import zk_logger

langsmith_project_name = config.configuration.get("langsmith_project_name", "zk-gpt")
langsmith_api_key = config.configuration.get("langsmith_api_key", "ls__2ba78d8aeab146a3939dbe190c1e7bfe")
langsmith_url = config.configuration.get("langsmith_url", "https://api.smith.langchain.com")
log_tag = "langsmith_adapter"
logger = zk_logger.logger


class LangsmithAdapter:
    langsmith_push_enabled = True
    langsmith_push_percentage = 100

    def __init__(self):
        self.langsmith_data_pusher_util = LangsmithDataPusherUtil(100, 100)

    def get_langsmith_tracing_callback(self):
        callbacks = []
        if self.langsmith_push_enabled and self.langsmith_data_pusher_util.can_push_data():
            langchain_tracer = LangChainTracer(project_name=langsmith_project_name, client=self.get_langsmith_client(),
                                               tags=self.get_langsmith_tag_list())
            callbacks.append(langchain_tracer)
        return callbacks

    @staticmethod
    def get_langsmith_client():
        return Client(api_url=langsmith_url,
                      api_key=langsmith_api_key)

    @staticmethod
    def get_langsmith_tag_list():
        # TODO : get tag list form configmap
        tag_list = ["zerok"]
        return tag_list

    @classmethod
    def update_langsmith_push_enabled(cls, push_enabled):
        current_datetime = datetime.datetime.now()
        logger.info(log_tag, f"updated the langsmith push enabled field to {push_enabled} at time : {current_datetime}")
        cls.langsmith_push_enabled = push_enabled

    @classmethod
    def get_langsmith_push_enabled(cls):
        return cls.langsmith_push_enabled


class LangsmithDataPusherUtil:
    def __init__(self, threshold_percentage, reset_after_calls=100):
        self.threshold_percentage = threshold_percentage
        self.call_count = 0
        self.pushed_count = 0
        self.reset_after_calls = reset_after_calls

    def can_push_data(self):
        self.call_count += 1
        if self.call_count > self.reset_after_calls:
            self.reset()
        if random.uniform(0, 100) <= self.threshold_percentage:
            self.pushed_count += 1
            return True
        return False

    def reset(self):
        self.call_count = 0
