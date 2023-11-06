from langchain.chains import LLMChain
from langchain.llms import OpenAI

from app import config
from app.utils import zk_logger

openai_api_key = config.configuration.get("openai_key", "")
openai__model = config.configuration.get("openai__model", "")
log_tag = "langchain_multichain_factory"
logger = zk_logger.logger


class LangChainMultichainFactory:
    def __init__(self):
        self.llm = OpenAI(model_name="gpt-3.5-turbo-16k", openai_api_key=openai_api_key, temperature=0.2)

    def generate_langchain_chain(self, prompt, output_key):
        # include type in prompt and write custom strategy to choose different llm for each promt type
        return LLMChain(llm=self.llm, prompt=prompt, output_key=output_key)

    def get_sequential_chains(self, prompts, output_keys):
        try:
            sequential_chains = []
            for i, prompt in enumerate(prompts):
                chain = self.generate_langchain_chain(prompt, output_keys[i])
                sequential_chains.append(chain)
            return sequential_chains
        except Exception as e:
            logger.error(log_tag, f"An error occurred: {e}")
            return []
