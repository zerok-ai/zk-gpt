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
import numpy as np
import json
import client


tiktoken.encoding_for_model('gpt-3.5-turbo')


#data 
# data = load_dataset("wikipedia", "20220301.simple", split='train[:10000]')
# data = np.loadtxt('app/temp.json')


data = ""

with open("app/temp.json",'r') as file: 
    data = json.load(file)


tokenizer = tiktoken.get_encoding('cl100k_base')

# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

tiktoken_len("hello I am a chunk of text and using the tiktoken_len function "
             "we can find the length of this chunk of text in tokens")


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=20,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)

# chunks = text_splitter.split_text(str(data))[:3]

# tiktoken_len(chunks[0]), tiktoken_len(chunks[1]), tiktoken_len(chunks[2])


# OPENAI_API_KEY = getpass("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")  # platform.openai.com

model_name = 'text-embedding-ada-002'


print("\n elbed ------------------------------------------------------------------------------------------------------------------------------------------------------- \n")
embed = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    openai_api_key="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"
)


texts = [
    'this is the first chunk of text',
    'then another second chunk of text is here'
]

index_name = 'zk-index'
pinecone.init(
    api_key="cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2",
    environment="us-west4-gcp-free"
)

if index_name not in pinecone.list_indexes():
    # we create a new index
    pinecone.create_index(
        name=index_name,
        metric='cosine',
        dimension=1536  # 1536 dim of text-embedding-ada-002
    )

index = pinecone.GRPCIndex(index_name)

batch_limit = 100
texts = []
metadatas = []

for i, (outer_key, inner_dict) in enumerate(tqdm(data.items())):
    for inner_key, inner_data in inner_dict.items():
        metadata = {
            'issue-id': str(outer_key),
            'incident-id': str(inner_key),
            'issue-title': "Issue_incident : {}_{}".format(str(outer_key),str(inner_key)) 
        }
        # now we create chunks from the record text
        record_texts = text_splitter.split_text(str(inner_data))
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
            embeds = embed.embed_documents(texts)
            index.upsert(vectors=zip(ids, embeds, metadatas))
            texts = []
            metadatas = []

        if len(texts) > 0:
            ids = [str(uuid4()) for _ in range(len(texts))]
            embeds = embed.embed_documents(texts)
            index.upsert(vectors=zip(ids, embeds, metadatas))   

text_field = "text"

# switch back to normal index for langchain
index = pinecone.Index(index_name)

vectorstore = Pinecone(
    index, embed.embed_query, text_field
)


query = ""

vectorstore.similarity_search(
    query,  # our search query
    k=3  # return 3 most relevant docs
)




# completion llm
llm = ChatOpenAI(
    openai_api_key="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",
    model_name='gpt-3.5-turbo',
    temperature=0.0
)

qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)
ans = qa.run(query)
print(str(ans))

# from langchain.chains import RetrievalQAWithSourcesChain

# qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
#     llm=llm,
#     chain_type="stuff",
#     retriever=vectorstore.as_retriever()
# )

# qa_with_sources(query)