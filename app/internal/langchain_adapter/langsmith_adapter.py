from langchain.callbacks import LangChainTracer
from langsmith import Client

from app import config

langsmith_project_name = config.configuration.get("langsmith_project_name", "zk-gpt")
langsmith_api_key = config.configuration.get("langsmith_api_key", "ls__2ba78d8aeab146a3939dbe190c1e7bfe")
langsmith_url = config.configuration.get("langsmith_url", "https://api.smith.langchain.com")


class LangsmithAdapter:

    def get_langsmith_tracing_callback(self):
        callbacks = []
        langchain_tracer = LangChainTracer(project_name=langsmith_project_name, client=self.get_langsmith_client(), tags=self.get_langsmith_tag_list())
        callbacks.append(langchain_tracer)
        return callbacks

    @staticmethod
    def get_langsmith_client():
        return Client(api_url=langsmith_url,
                      api_key=langsmith_api_key)

    @staticmethod
    def get_langsmith_tag_list():
        # TODO : get tag list form configmap
        tag_list = ["zerok", "glance"]
        return tag_list
