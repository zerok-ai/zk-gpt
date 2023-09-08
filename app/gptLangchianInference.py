from langchain.llms import OpenAI 
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage , SystemMessage
from langchain.chains import LLMChain , SimpleSequentialChain
from langchain import PromptTemplate
import dataDao
import promptFactory
import langchianMultiChainFactory


# TODO : move this to init method
llm = OpenAI(model_name="gpt-3.5-turbo")
promptFactInstance =  promptFactory.PromptFactory()
langchianMultiChainFact = langchianMultiChainFactory.LangChainMultichainFactory()

class LangChainInference():

    def getGPTLangchainInference(issue_id,incident_id,issuedata):
        print("Inferencing the issue data using langchain for issue id : {} and incident id: {}".format(issue_id,incident_id))  #modify the print statement

        prompts = promptFactInstance.generatePromptsForSequentialChain()

        sequentialListChains = langchianMultiChainFact.getSequentialChains(prompts)

        overall_chain = SimpleSequentialChain(sequentialListChains, verbose=True)

        final_issue_inference  = overall_chain.run("large language model")
        
        return final_issue_inference
        

# from langchain import PromptTemplate

# template = """
# Prompt for the summary till now 
# {input} and the prompt for the data we are sending now {custom_data}
# """

# prompt = PromptTemplate(
#     input_variables=["input","custom_data"],
#     template=template,
# )

# llm(prompt.format(concept="large language model"))

# from langchain.chains import LLMChain
# chain = LLMChain(llm=llm, prompt=prompt)

# # Run the chain only specifying the input variable.
# print(chain.run("large language model"))  

# second_prompt = PromptTemplate(
#     input_variables=["ml_concept"],
#     template="Turn the concept description of {ml_concept} and explain it to me like I'm five in 500 words",
# )
# chain_two = LLMChain(llm=llm, prompt=second_prompt)




# messages = [
#     SystemMessage(content="You are a helpful email assistant"),
#     HumanMessage(content="Write an email to my landlord asking him for a rent decrease")
# ]

# response=chat(messages)
# print(response.content,end='\\n')


# Import and initialize Pinecone client
'''
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 100,
    chunk_overlap  = 0,
)
texts = text_splitter.create_documents([explanation])

# Import and instantiate OpenAI embeddings
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model_name="ada")
# Turn the first text chunk into a vector with the embedding
query_result = embeddings.embed_query(texts[0].page_content)
print(query_result)
# output :

import os
import pinecone
from langchain.vectorstores import Pinecone
pinecone.init(
    api_key=os.getenv('PINECONE_API_KEY'),
    environment=os.getenv('PINECONE_ENV')
)

# Upload vectors to Pinecone
index_name = "langchain-quickstart"
search = Pinecone.from_documents(texts, embeddings, index_name=index_name)

query = "Why is there all this hype about large language models?"
result = search.similarity_search(query)
print(result)
'''

# Import Python REPL tool and instantiate Python agent
# TODO : AGENT
'''
from langchain.agents.agent_toolkits import create_python_agent
from langchain.tools.python.tool import PythonREPLTool
from langchain.python import PythonREPL
from langchain.llms.openai import OpenAI
agent_executor = create_python_agent(
    llm=OpenAI(temperature=0, max_tokens=1000),
    tool=PythonREPLTool(),
    verbose=True
)
agent_executor.run("What is the 10th fibonacci number?")

'''