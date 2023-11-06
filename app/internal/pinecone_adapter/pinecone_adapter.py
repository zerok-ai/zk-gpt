import concurrent.futures
from uuid import uuid4

import pinecone
import tiktoken
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone

from app import config
from app.clients import axon_client
from app.utils import zk_logger

log_tag = "pinecone_adapter"
logger = zk_logger.logger

openai_key = config.configuration.get("openai_key", "")
pinecone_index_key = config.configuration.get("pinecone_index", "zk-index-prod")
pinecone_api_key = config.configuration.get("pinecone_key", "cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2")
pinecone_environment = config.configuration.get("pinecone_env", "us-west4-gcp-free")
user_qna_openai_temp = config.configuration.get("user_qna_openai_temp", 0.4)
user_qna_topk = config.configuration.get("user_qna_topk", 500)


class PineconeAdapter:
    def __init__(self):
        self.issueVectorization = Vectorization()

    def vectorize_data_and_push_to_pinecone_db(self, issue_id, incident_id, data_list):
        # initialize and push to vector db
        # Use a ThreadPoolExecutor with 5 worker threads (you can adjust the number as needed)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Create a list of arguments for vectorize_and_push_wrapper
            args_list = [(issue_id, incident_id, data) for data in data_list]

            # Submit tasks for vectorizing data
            executor.map(self.vectorize_and_push_wrapper, args_list)

        # print(f"All vectorizing complete for issue Id: {issue_id}, incident_id: {incident_id}\n")
        # for data in data_list:
        #     self.issueVectorization.vectorize_data_and_push(issue_id, incident_id, data)
        # print("vectorizing complete for issue Id : {}, incident_id: {} \n".format(issue_id, incident_id))

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
        response = self.issueVectorization.get_gpt_inference_using_vector_db_custom_params(query, issue, temperature,
                                                                                           top_k)
        return response

    def get_similar_docs_for_given_query(self, issue_id, query):
        similar_pinecone_docs = self.issueVectorization.get_similar_pinecone_docs_for_query(query, issue_id)
        return similar_pinecone_docs

    def vectorize_and_push_wrapper(self, args):
        issue_id, incident_id, data = args
        self.issueVectorization.vectorize_data_and_push(issue_id, incident_id, data)


class Vectorization:
    def __init__(self):
        self.embed = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=config.configuration.get("openai_key", "")
        )
        self.index_name = pinecone_index_key
        self.axon_svc_client = axon_client.AxonServiceClient()
        logger.info(log_tag, "Initiating pinecone : \n")
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
            logger.info(log_tag, "vectororing attempt for the NULL data for issue_id : {} , incident_id: {}".format(issue_id,
                                                                                                     incident_id))
            return
        if data['payload'] is None:
            logger.info(log_tag, "vectororing attempt for the NULL payload for issue_id : {} , incident_id: {}".format(issue_id,
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
        metadata = []
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
        metadata.extend(record_metadatas)
        # if we have reached the batch_limit we can add texts
        if len(texts) >= batch_limit:
            ids = [str(uuid4()) for _ in range(len(texts))]
            embeds = self.embed.embed_documents(texts)
            self.index.upsert(vectors=zip(ids, embeds, metadata))
            texts = []
            metadata = []

        if len(texts) > 0:
            ids = [str(uuid4()) for _ in range(len(texts))]
            embeds = self.embed.embed_documents(texts)
            self.index.upsert(vectors=zip(ids, embeds, metadata))

    def get_gpt_inference_using_vector_db(self, query, issue_id, incident_id):
        logger.info(log_tag,
            "fetching the top vectors form the vector DB for issue: {}, incident_id: {}, specific to query: {}".format(
                issue_id, incident_id, query))
        # write logic to fetch from vector DB.
        vector_store = self.get_vector_store(issue_id, incident_id, query)
        retrieval_qa = self.initialize_llm_model_and_vector_retrieval(vector_store)
        ans = retrieval_qa.run(query)
        response = "Query : {}\n".format(query)
        response += "Answer : {}\n".format(str(ans))
        return str(ans)

    def fetch_data_and_vectorize_issue(self, issue):
        logger.info(log_tag, "vectoring issue with issue Id : {} \n".format(issue))
        # write vectorization logic
        # get issue summary
        issue_data = dict()

        issue_summary = self.axon_svc_client.get_issue_summary(issue)

        # get all incidents for the given issue
        issue_incidents = self.axon_svc_client.get_issue_incidents(issue)

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
        for incident in issue_incidents:
            spans_map = self.axon_svc_client.get_spans_map(issue, incident)
            exception_map = []
            req_payload_map = []
            res_payload_map = []
            for span_id in spans_map:
                span_raw_data = self.axon_svc_client.get_span_raw_data(issue, incident, span_id)
                if span_raw_data is not None:
                    spans_map[span_id].update(span_raw_data)

            filtered_spans_map = dict()
            for spanId in spans_map:
                # remove error key from spanMap
                del spans_map[spanId]["error"]

                span = spans_map[spanId]
                span["span_id"] = spanId
                # remove exception span from spanMap
                if str(span["protocol"]).upper() == "EXCEPTION":
                    parentSpanId = span["parent_span_id"]
                    if parentSpanId in spans_map:
                        spans_map[parentSpanId]["exception"] = span.get("req_body")
                        exception_map.append(span.get("req_body"))
                        filtered_spans_map[parentSpanId] = spans_map[parentSpanId]
                else:
                    filtered_spans_map[spanId] = span

            for spanId in filtered_spans_map:
                span = spans_map[spanId]
                req_payload_map.append(span.get('req_body'))
                res_payload_map.append(span.get('resp_body'))

            metadata = {
                'issue-id': str(issue),
                'source': str(issue),
                'incident-id': str(incident),
                'issue-title': "Issue_incident : {}_{}".format(str(issue), str(incident))
                # 'cluster':
                # 'clustomer-id'
            }

            # issue data creation
            issue_data['spans'] = filtered_spans_map
            issue_data['stackTrace'] = exception_map
            issue_data['request_payload'] = req_payload_map
            issue_data['response_payload'] = res_payload_map
            issue_data['issueSummary'] = issue_summary
            issue_data['metadata'] = metadata

            texts = []
            metadata = []

            # now we create chunks from the record text
            record_texts = text_splitter.split_text(str(issue_data))
            # create individual metadata dicts for each chunk
            record_metadatas = [{
                "chunk": j, "text": text, **metadata
            } for j, text in enumerate(record_texts)]
            # append these to current batches
            texts.extend(record_texts)
            metadata.extend(record_metadatas)
            # if we have reached the batch_limit we can add texts
            if len(texts) >= batch_limit:
                ids = [str(uuid4()) for _ in range(len(texts))]
                embeds = self.embed.embed_documents(texts)
                self.index.upsert(vectors=zip(ids, embeds, metadata))
                texts = []
                metadata = []

            if len(texts) > 0:
                ids = [str(uuid4()) for _ in range(len(texts))]
                embeds = self.embed.embed_documents(texts)
                self.index.upsert(vectors=zip(ids, embeds, metadata))

        logger.info(log_tag, "vectorzing complete for issue Id : {} \n".format(issue))

    def get_gpt_inference_using_vector_db_custom_params(self, query, issue, temperature, k):

        logger.info(log_tag, "fetching the top {} vectors form the vector DB specific to  query".format(k))
        # write logic to fetch from vector DB.
        vector_store = self.get_vector_store(issue, None, query)
        retrieval_qa = self.initialize_llm_model_and_vector_retrieval(vector_store)
        ans = retrieval_qa.run(query)
        response = "Query : {}\n".format(query)
        response += "Answer : {}\n".format(str(ans))
        return str(ans)

    def get_vector_store(self, issue_id, incident_id, query):
        text_field = "text"
        # switch back to normal index for langchain
        vectorstore = Pinecone(
            index=pinecone.Index(self.index_name), embedding=self.embed.embed_query, text_key=text_field
        )
        if incident_id is None:
            metadata_filter = {"issue_id": {'$eq': issue_id}}
        else:
            metadata_filter = {"issue_id": {'$eq': issue_id}, "incident_id": {'$eq': incident_id}}

        docs = vectorstore.similarity_search(
            query,  # our search query
            k=user_qna_topk,  # return k most relevant docs
            filter=metadata_filter,
        )
        return vectorstore, docs

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
        text_field = "text"
        # switch back to normal index for langchain
        vectorstore = Pinecone(
            pinecone.Index(self.index_name), self.embed.embed_query, text_field
        )

        metadata_filter = {"source": {'$eq': str(issue_id)}}

        docs = vectorstore.similarity_search(
            query,  # our search query
            k=user_qna_topk,  # return k most relevant docs
            filter={
                "issue_id": {"$eq": str(issue_id)}
            }
        )
        return docs
