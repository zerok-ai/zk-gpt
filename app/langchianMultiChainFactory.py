from langchain.llms import OpenAI 
from langchain.chains import LLMChain , SimpleSequentialChain
import openai
import config

openai_api_key = config.configuration.get("openai_key", "")
openai__model = config.configuration.get("openai__model", "")

class LangChainMultichainFactory():
    def __init__ (self): 
        self.llm = OpenAI(model_name="gpt-3.5-turbo-16k",openai_api_key=openai_api_key,temperature=0.2)

    def generateLangchainChain(self,prompt,output_key):
        # include type in prompt and write custom strategy to choose different llm for each promt type
        return LLMChain(llm=self.llm, prompt=prompt,output_key=output_key)

    def getSequentialChains(self,prompts,output_keys):
        try: 
            sequential_chains = []
            for i,prompt in enumerate(prompts):
                chain = self.generateLangchainChain(prompt,output_keys[i])
                sequential_chains.append(chain)
            return sequential_chains
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

