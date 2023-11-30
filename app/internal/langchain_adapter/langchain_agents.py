from langchain.agents import AgentType, initialize_agent, load_tools
from langchain.chat_models import ChatOpenAI
from app import config

openai_api_key = config.configuration.get("openai_key", "")
llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", openai_api_key=openai_api_key, temperature=0.1)

# load tools
tools = load_tools(["serpapi", "llm-math"], llm=llm)


# zeroshot agent using ReAct : https://arxiv.org/pdf/2210.03629.pdf
class LangchainAgentAdapter:
    description: str = "Langchain agent adapter to "

    def __int__(self):
        print("langchain agent adapter")

    def get_langchain_agent_specific_task(self) -> None:
        print("langchain agent specific to task")
        return None

    def get(self):
        temp = self.get_langchain_agent_specific_task()
        print(temp)
