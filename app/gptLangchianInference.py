from langchain.llms import OpenAI 
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage , SystemMessage
from langchain.chains import LLMChain , SimpleSequentialChain , SequentialChain
from langchain import PromptTemplate
import dataDao
import promptFactory
import langchianMultiChainFactory
import config
class LangChainInference():
    def __init__ (self): 
        self.promptFactInstance = promptFactory.PromptFactory()
        self.langchianMultiChainFact = langchianMultiChainFactory.LangChainMultichainFactory()
    
    def getGPTLangchainInference(self,issue_id,incident_id,custom_data):
        try: 
            print("Inferencing the issue data using langchain for issue id : {} and incident id: {} \n".format(issue_id,incident_id))  #modify the print statement
            prompts ,output_keys = self.promptFactInstance.generatePromptsForSequentialChain()

            sequentialListChains = self.langchianMultiChainFact.getSequentialChains(prompts,output_keys)
        
            overall_chain = SequentialChain(chains = sequentialListChains, verbose=True,input_variables=["issue_prompt","issue_data","trace_data","exception_data","req_res_data"],output_variables=["issue_summary","trace_summary","exception_summary","final_summary"])
        
            final_issue_inference  = overall_chain(custom_data)
            
            return final_issue_inference
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
        