import pinecone
import os
pinecone.init(api_key="cc77b1e4-3ec0-4b4f-a3eb-93453e1c43c2", environment="us-west4-gcp-free")
index=pinecone.Index(index_name="zk-index")
import pandas as pd

df = pd.DataFrame(
     data={
         "id": ["A", "B", "C", "D", "E"],
         "vector":[
           [1.,1.,1.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [1.,2.,3.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [2.,1.,1.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [3.,2.,1.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
           [2.,2.,2.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]]
     })
df
# index.upsert(vectors=zip(df.id,df.vector),namespace="zk-llm")
index.describe_index_stats()
temp = index.query(
        queries=[[1.,2.,3.,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]],
        top_k=3,
        include_values=True,namespace="zk-llm")


print(temp)