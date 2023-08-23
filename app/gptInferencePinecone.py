import tiktoken
from datasets import load_dataset
from getpass import getpass
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from tqdm.auto import tqdm
from uuid import uuid4
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
import client
import config

openai_api_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index_key","zk-index")
pinecone_api_key=config.configuration.get("pinecone_api_key","cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment=config.configuration.get("pinecone_environment","us-west4-gcp-free")

class GptInferencePineconeVectorDb:
    def __init__ (self): 
        self.issuesInVectorDB = dict()  
        self.issueVectorization = IssueVectorization()  

    def vectorizeIncidentAndPushtoVectorDb(self , issue): 
        self.issuesInVectorDB[issue] = dict({"status": "VECTORIZATION_IN_PROGRESS","issue":{issue}})
        #inisialize and push to vector db
        self.issueVectorization.vectorsizeIssue(issue)
        self.issuesInVectorDB[issue]['status'] = "VECTORIZATION_COMPLETE"
        return self.issuesInVectorDB[issue]
    
    def hasIssueInDb(self, issue):
        print("hasIssue | " + issue)
        findIssue = client.findIfIssueIsPresentInDb(issue)
        if findIssue is False: 
            return False
        else: 
            return True 

    def getGptInferencesForQuery(self,issue,query,temperature,topK):
        respone = self.issueVectorization.getGptInferenceUsingVectorDB(query,issue,temperature,topK)
        return respone
    
class IssueVectorization:
    def __init__ (self): 
        self.embed = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key
        )
        self.index_name = pinecone_index_key
        print("Initiating pinecone : ")
        pinecone.init(
            api_key=pinecone_api_key,
            environment=pinecone_environment
        )
        if self.index_name not in pinecone.list_indexes():
        # we create a new index
            pinecone.create_index(
                name=self.index_name,
                metric='cosine',
                dimension=1536  # 1536 dim of text-embedding-ada-002
            )

        self.index = pinecone.GRPCIndex(self.index_name)
        print("pinecone index stats : " ) 
        print(str(self.index.describe_index_stats()))
        print("\n")
        
    
    def vectorsizeIssue(self,issue): 
        print("vectorzing issue with issue Id : {} \n".format(issue))
        #write vectorization logic
        # get issue summary
        issueData  = dict()
        
        issueSummary = client.getIssueSummary(issue)

        # get all incidents for the given issue
        issueIncidents = client.getIssueIncidents(issue)

        # vector pushing logic starts here

        tiktoken.encoding_for_model('gpt-3.5-turbo')
        tokenizer = tiktoken.get_encoding('cl100k_base')
        # create the length function
        def tiktoken_len(text):
            tokens = tokenizer.encode(
                text,
                disallowed_special=()
            )
            return len(tokens)
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=30,
            length_function=tiktoken_len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        batch_limit = 100
        
        # for each incident create data and push to vector DB : 
        for incident in issueIncidents:
            spansMap = client.getSpansMap(issue, incident)
            exceptionMap = []
            reqPayloadMap = []
            resPayloadMap = []
            for span_id in spansMap:
                spanRawData = client.getSpanRawdata(issue, incident, span_id)
                spansMap[span_id].update(spanRawData)

            filteredSpansMap = dict()
            for spanId in spansMap:
                # remove error key from spanMap
                del spansMap[spanId]["error"]

                span = spansMap[spanId]
                span["span_id"] = spanId
                # remove exception span from spanMap
                if str(span["protocol"]).upper() == "EXCEPTION":
                    parentSpanId = span["parent_span_id"]
                    if parentSpanId in spansMap:
                        spansMap[parentSpanId]["exception"] = span["request_payload"]
                        exceptionMap.append(span["request_payload"])
                        filteredSpansMap[parentSpanId] = spansMap[parentSpanId]
                else:
                    filteredSpansMap[spanId] = span
            
            for spanId in filteredSpansMap:
                span = spansMap[spanId]
                reqPayloadMap.append(span['request_payload'])
                resPayloadMap.append(span['response_payload'])

            
            metadata = {
                'issue-id': str(issue),
                'source': str(issue),
                'incident-id': str(incident),
                'issue-title': "Issue_incident : {}_{}".format(str(issue),str(incident)) 
            }

            # issue data creation
            issueData['spans'] = filteredSpansMap
            issueData['stackTrace'] = exceptionMap
            issueData['request_payload'] = reqPayloadMap
            issueData['response_payload'] = resPayloadMap
            issueData['issueSummary'] = issueSummary
            issueData['metadata'] = metadata

            texts = []
            metadatas = []

            # now we create chunks from the record text
            record_texts = text_splitter.split_text(str(issueData))
            # create individual metadata dicts for each chunk
            record_metadatas = [{
                "chunk": j, "text": text, **metadata
            } for j, text in enumerate(record_texts)]
            # append these to current batches
            texts.extend(record_texts)
            metadatas.extend(record_metadatas)
            # if we have reached the batch_limit we can add texts
            if len(texts) >= batch_limit:
                ids = [str(uuid4()) for _ in range(len(texts))]
                embeds = self.embed.embed_documents(texts)
                self.index.upsert(vectors=zip(ids, embeds, metadatas))
                texts = []
                metadatas = []

            if len(texts) > 0:
                ids = [str(uuid4()) for _ in range(len(texts))]
                embeds = self.embed.embed_documents(texts)
                self.index.upsert(vectors=zip(ids, embeds, metadatas)) 

        print("vectorzing complete for issue Id : {} \n".format(issue))


    def getGptInferenceUsingVectorDB(self,query,issue,temperature,k): 

        print("fetching the top {} vectors form the vector DB specific to  query".format(k))
        #write logic to fetch from vector DB.
        vectorStore = self.getVectorStore(issue,k,query)
        retrievalQA = self.initializeLlmModelAndVectorRetrieval(temperature,vectorStore)
        ans = retrievalQA.run(query)
        response = "Query : {}\n".format(query)
        response+="Answer : {}\n".format(str(ans))
        print(response)
        return str(ans)


    def getVectorStore(self,issue,k,query):

        text_field = "text"
        # switch back to normal index for langchain
        vectorstore = Pinecone(
            pinecone.Index(self.index_name), self.embed.embed_query, text_field
        )
        metadata_filter = {"issue-id": issue,"source" : issue}
        vectorstore.similarity_search(
            query,  # our search query
            k=k, # return k most relevant docs
            filter=metadata_filter,
        )
        return vectorstore
    
    def initializeLlmModelAndVectorRetrieval(self,temperature,vectorStore):
        llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name='gpt-3.5-turbo',
            temperature=temperature
        )
        retrievalQA = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorStore.as_retriever()
        )
        return retrievalQA
    

    
    

    


    
