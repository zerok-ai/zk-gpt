"""
CLASS OVERVIEW 
Library to initiatiate all the LLM chain's during using the init method while the service is booting 

things it does : 
read promt library and create specific LLM chains 
and store inmemory DB 

and methods such as giving the langchain wrt to query class type

"""
from langchain.llms import OpenAI 
from langchain.chains import LLMChain , SimpleSequentialChain
import openai
import config

openai.api_key = config.configuration.get("openai_key", "")

class LangChainMultichainFactory():

    llm = OpenAI(model_name="gpt-3.5-turbo")

    def generateLangchainChain(self,prompt):
        # include type in prompt and write custom strategy to choose different llm for each promt type
        return LLMChain(llm=self.llm, prompt=prompt)

    def getSequentialChains(self,prompts): 
        try: 
            print("") #write proper print statement
            sequential_chains = []
            for prompt in prompts: 
                print("")
                chain = self.generateLangchainChain(prompt)
                sequential_chains.append(chain)
            return sequential_chains
        except Exception as e:
            print(f"An error occurred: {e}")
            return []





# from langchain.chains.router import MultiRouteChain, RouterChain
# from langchain.chat_models import ChatOpenAI
# from langchain.llms import OpenAI 
# from langchain.chains import ConversationChain
# from langchain.chains.llm import LLMChain
# from langchain.prompts import PromptTemplate

# from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser
# from langchain.chains.router.multi_prompt_prompt import MULTI_PROMPT_ROUTER_TEMPLATE
# from langchain.chains import SimpleSequentialChain, TransformChain

# from prompt_toolkit import HTML, prompt
# import langchain.callbacks

# from replace_function import create_transform_func

# langchain.callbacks.StdOutCallbackHandler

# from FileCallbackHandler import FileCallbackHandler

# from pathlib import Path
# from typing import Mapping, List, Union

# import promptFactory

# file_ballback_handler = FileCallbackHandler(Path('router_chain.txt'), print_prompts=True)

# class Config(): 
#     model = 'gpt-3.5-turbo-0613'
#     llm = OpenAI(model=model, temperature=0)

# cfg = Config()

# class MyMultiPromptChain(MultiRouteChain):
#     """A multi-route chain that uses an LLM router chain to choose amongst prompts."""

#     router_chain: RouterChain
#     """Chain for deciding a destination chain and the input to it."""
#     destination_chains: Mapping[str, Union[LLMChain, SimpleSequentialChain]]
#     """Map of name to candidate chains that inputs can be routed to."""
#     default_chain: LLMChain
#     """Default chain to use when router doesn't map input to one of the destinations."""

#     @property
#     def output_keys(self) -> List[str]:
#         return ["text"]


# def generate_destination_chains():
#     """
#     Creates a list of LLM chains with different prompt templates.
#     Note that some of the chains are sequential chains which are supposed to generate unit tests.
#     """
#     prompt_factory = promptFactory.PromptFactory()

#     destination_chains = {}
#     destination_chains_list = []
#     for p_info in prompt_factory.prompt_infos:
#         name = p_info['name']
#         prompt_template = p_info['prompt_template']
        
#         destination_chains[name] = LLMChain(
#             llm=cfg.llm, 
#             prompt=PromptTemplate(template=prompt_template, input_variables=['input']),
#             output_key='text'
#         )
#         destination_chains_list.append(destination_chains[name])
    
#     destination_chains['aggreagate_issue_summary'] = SimpleSequentialChain(
#         chains=destination_chains_list, verbose=True, output_key='text', callbacks=[file_ballback_handler]
#     )
#     # add more chains according to usecase
#     default_chain = ConversationChain(llm=cfg.llm, output_key="text")
#     return prompt_factory.prompt_infos, destination_chains, default_chain


# def generate_router_chain(prompt_infos, destination_chains, default_chain):
#     """
#     Generats the router chains from the prompt infos.
#     :param prompt_infos The prompt informations generated above.
#     :param destination_chains The LLM chains with different prompt templates
#     :param default_chain A default chain
#     """
#     destinations = [f"{p['name']}: {p['description']}" for p in prompt_infos]
#     destinations_str = '\n'.join(destinations)
#     router_template = MULTI_PROMPT_ROUTER_TEMPLATE.format(destinations=destinations_str)
#     router_prompt = PromptTemplate(
#         template=router_template,
#         input_variables=['input'],
#         output_parser=RouterOutputParser()
#     )
#     router_chain = LLMRouterChain.from_llm(cfg.llm, router_prompt)
#     multi_route_chain = MyMultiPromptChain(
#         router_chain=router_chain,
#         destination_chains=destination_chains,
#         default_chain=default_chain,
#         verbose=True, 
#         callbacks=[file_ballback_handler]
#     )
#     return multi_route_chain
    


# if __name__ == "__main__":
#     # Put here your API key or define it in your environment
#     # os.environ["OPENAI_API_KEY"] = '<key>'

#     prompt_infos, destination_chains, default_chain = generate_destination_chains()
#     chain = generate_router_chain(prompt_infos, destination_chains, default_chain)
#     with open('conversation.log', 'w') as f:
#         while True:
#             question = prompt(
#                 HTML("<b>Type <u>Your question</u></b>  ('q' to exit, 's' to save to html file): ")
#             )
#             if question == 'q':
#                 break
#             if question in ['s', 'w'] :
#                 file_ballback_handler.create_html()
#                 continue
#             result = chain.run(question)
#             f.write(f"Q: {question}\n\n")
#             f.write(f"A: {result}")
#             f.write('\n\n ====================================================================== \n\n')
#             print(result)
#             print()


