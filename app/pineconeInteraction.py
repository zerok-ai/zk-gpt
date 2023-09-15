import tiktoken
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from uuid import uuid4
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config
import client

openai_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index", "zk-index-prod")
pinecone_api_key = config.configuration.get("pinecone_key", "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment = config.configuration.get("pinecone_env", "us-west4-gcp-free")
user_qna_openai_temp = config.configuration.get("user_qna_openai_temp", 0.4)
user_qna_topk = config.configuration.get("user_qna_topk", 10)


class PineconeInteraction:
    def __init__(self):
        self.issueVectorization = Vectorization()

    def vectorize_data_and_pushto_pinecone_db(self, issue_id, incident_id, data_list):
        # initialize and push to vector db
        for data in data_list:
            self.issueVectorization.vectorize_data_and_push(issue_id, incident_id, data)
        print("vectorzing complete for issue Id : {}, incident_id: {} \n".format(issue_id, incident_id))

    @staticmethod
    def create_pinecone_data(issue_id, incident_id, data_type, category, data, client_id, cluster):
        data = {
            "issue_id": issue_id,
            "incident_id": incident_id,
            "payload": data,
            "type": data_type,
            "category": category,
            "client_id": client_id,
            "cluster": cluster
        }
        return data

    def vectorize_issue_and_pushtu_pinecone_db(self, issue):
        self.issueVectorization.fetch_data_and_vectorize_issue(issue)

    def get_gpt_inferences_for_query_custom_data(self, issue, query, temperature, top_k):
        response = self.issueVectorization.getGptInferenceUsingVectorDBCustomParams(query, issue, temperature, top_k)
        return response

    def get_similar_docs_for_given_query(self, issue_id, query):
        similar_pinecone_docs = self.issueVectorization.get_similar_pinecone_docs_for_query(query, issue_id)
        return similar_pinecone_docs


class Vectorization:
    def __init__(self):
        self.embed = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=config.configuration.get("openai_key", "")
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
        print("pinecone index stats : \n")
        print(str(self.index.describe_index_stats()))

    def vectorize_data_and_push(self, issue_id, incident_id, data):

        """
        data should of this form : 
        data = {
        "issue_id" : "issue_id",
        "incident_id" : "incident_id",
        "payload" : {},
        "type" : "type",
        "category": category,
        "client_id" : "client",
        "cluster" : "cluster"
        }
        """

        if data is None:
            print("vectororing attempt for the NULL data for issue_id : {} , incident_id: {}".format(issue_id,
                                                                                                     incident_id))
            return
        if data['payload'] is None:
            print("vectororing attempt for the NULL payload for issue_id : {} , incident_id: {}".format(issue_id,
                                                                                                        incident_id))
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
            'issue_title': "Issue_incident : {}_{}".format(str(issue_id), str(incident_id)),
            "type": "default" if data['type'] is None else data['type'],
            "category": "default" if data['category'] is None else data['category'],
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

    def getGptInferenceUsingVectorDB(self, query, issue_id, incident_id):
        print(
            "fetching the top vectors form the vector DB for issue: {}, incident_id: {}, specific to query: {}".format(
                 issue_id, incident_id, query))
        # write logic to fetch from vector DB.
        vector_store = self.getVectorStore(issue_id, incident_id, query)
        retrieval_qa = self.initialize_llm_model_and_vector_retrieval(vector_store)
        ans = retrieval_qa.run(query)
        response = "Query : {}\n".format(query)
        response += "Answer : {}\n".format(str(ans))
        print(response)
        return str(ans)

    def fetch_data_and_vectorize_issue(self, issue):
        print("vectoring issue with issue Id : {} \n".format(issue))
        # write vectorization logic
        # get issue summary
        issueData = dict()

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
            chunk_size=500,
            chunk_overlap=50,
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
                        spansMap[parentSpanId]["exception"] = span["req_body"]
                        exceptionMap.append(span["req_body"])
                        filteredSpansMap[parentSpanId] = spansMap[parentSpanId]
                else:
                    filteredSpansMap[spanId] = span

            for spanId in filteredSpansMap:
                span = spansMap[spanId]
                reqPayloadMap.append(span['req_body'])
                resPayloadMap.append(span['resp_body'])

            metadata = {
                'issue-id': str(issue),
                'source': str(issue),
                'incident-id': str(incident),
                'issue-title': "Issue_incident : {}_{}".format(str(issue), str(incident))
                # 'cluster': 
                # 'clustomer-id'
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

    def getGptInferenceUsingVectorDBCustomParams(self, query, issue, temperature, k):

        print("fetching the top {} vectors form the vector DB specific to  query".format(k))
        # write logic to fetch from vector DB.
        vectorStore = self.getVectorStore(issue, None, query)
        retrievalQA = self.initialize_llm_model_and_vector_retrieval(vectorStore)
        ans = retrievalQA.run(query)
        response = "Query : {}\n".format(query)
        response += "Answer : {}\n".format(str(ans))
        print(response)
        return str(ans)

    def getVectorStore(self, issue_id, incident_id, query):
        text_field = "text"
        # switch back to normal index for langchain
        vectorstore = Pinecone(
            pinecone.Index(self.index_name), self.embed.embed_query, text_field
        )
        if incident_id is None:
            metadata_filter = {"issue_id": {'$eq': issue_id}}
        else:
            metadata_filter = {"issue_id": {'$eq': issue_id}, "incident_id": {'$eq': incident_id}}

        vectorstore.similarity_search(
            query,  # our search query
            k=user_qna_topk,  # return k most relevant docs
            filter=metadata_filter,
        )
        return vectorstore

    @staticmethod
    def initialize_llm_model_and_vector_retrieval(vector_store):
        llm = ChatOpenAI(
            openai_api_key=openai_key,
            model_name='gpt-3.5-turbo-16k',
            temperature=user_qna_openai_temp
        )
        retrievalQA = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )
        return retrievalQA

    def get_similar_pinecone_docs_for_query(self, query, issue_id):
        metadata_filter = {"issue_id": {'$eq': issue_id}}
        similar_docs = self.index_name.similarity_search_with_score(query, k=10, filter=metadata_filter)
        return similar_docs
