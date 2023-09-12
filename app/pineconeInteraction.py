import tiktoken
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from uuid import uuid4
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
import client
import config

openai_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index","zk-index-prod")
pinecone_api_key=config.configuration.get("pinecone_key","cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment=config.configuration.get("pinecone_env","us-west4-gcp-free")
user_qna_openai_temp = config.configuration.get("user_qna_openai_temp",0.4)
user_qna_topk = config.configuration.get("user_qna_topk",10)

class PineconeInteraction:
    def __init__ (self): 
        self.issueVectorization = Vectorization()  

    def vectorizeDataAndPushtoPineconeDB(self , issue_id, incident_id, data): 
        #inisialize and push to vector db
        self.issueVectorization.vectorsizeIssue(issue_id, incident_id, data)

    def getGptInferencesForQueryForPineconeData(self,issue,query,temperature,topK):
        respone = self.issueVectorization.getGptInferenceUsingVectorDB(query,issue,temperature,topK)
        return respone
    
class Vectorization:
    def __init__ (self): 
        self.embed = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key= config.configuration.get("openai_key", "")
        )
        self.index_name = pinecone_index_key
        print("Initiating pinecone : \n")
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

        self.index = pinecone.Index(self.index_name)
        print("pinecone index stats : \n" ) 
        print(str(self.index.describe_index_stats()))
        
    def vectorsizeIssue(self, issue_id, incident_id, data): 
        issueData  = dict()

        """
        data should of this form : 
        data = {
        "issue_id" : "issue_id",
        "incident_id" : "incident_id",
        "payload" : {},
        "type" : "type",
        "client_id" : "client",
        "cluster" : "cluster"
        }
        """

        if data is None: 
            print("vectororing attempt for the NULL data for issue_id : {} , incident_id: {}".format(issue_id, incident_id))
            return 
        if data['payload'] is None:
            print("vectororing attempt for the NULL payload for issue_id : {} , incident_id: {}".format(issue_id, incident_id))
            return 

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
            chunk_size=500,
            chunk_overlap=50,
            length_function=tiktoken_len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        batch_limit = 100
        
        texts = []
        metadatas = []
        metadata = {
            'issue_id': str(issue_id),
            'source': str(issue_id),
            'incident_id': str(incident_id),
            'issue_title': "Issue_incident : {}_{}".format(str(issue_id),str(incident_id)),
            "type" : "default" if data['type'] is None else data['type'],
            "cluster": "default" if data['cluster'] is None else data['cluster'],
            "client_id": "default" if data['client_id'] is None else data['client_id']
        }

        # now we create chunks from the record text
        record_texts = text_splitter.split_text(str(data['payload']))
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

        print("vectorzing complete for issue Id : {}, incident_id: {} \n".format(issue_id,incident_id))

    def getGptInferenceUsingVectorDB(self,query,issue_id,incident_id): 
        print("fetching the top {} vectors form the vector DB for issue: {}, incident_id: {}, specific to query: {}".format(k, issue_id, incident_id, query))
        #write logic to fetch from vector DB.
        vectorStore = self.getVectorStore(issue_id,incident_id,query)
        retrievalQA = self.initializeLlmModelAndVectorRetrieval(vectorStore)
        ans = retrievalQA.run(query)
        response = "Query : {}\n".format(query)
        response+="Answer : {}\n".format(str(ans))
        print(response)
        return str(ans)

    def getVectorStore(self,issue_id,incident_id,query):
        text_field = "text"
        # switch back to normal index for langchain
        vectorstore = Pinecone(
            pinecone.Index(self.index_name), self.embed.embed_query, text_field
        )
        metadata_filter = {"issue_id": {'$eq': issue_id},"incident_id": {'$eq': incident_id}}
        vectorstore.similarity_search(
            query,  # our search query
            k=user_qna_topk, # return k most relevant docs
            filter=metadata_filter,
        )
        return vectorstore
    
    def initializeLlmModelAndVectorRetrieval(self,vectorStore):
        llm = ChatOpenAI(
            openai_api_key=openai_key,
            model_name='gpt-3.5-turbo-16k',
            temperature=user_qna_openai_temp
        )
        retrievalQA = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorStore.as_retriever()
        )
        return retrievalQA