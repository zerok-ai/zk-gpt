import json
from tqdm.auto import tqdm

from langchain.embeddings.openai import OpenAIEmbeddings


model_name = 'text-embedding-ada-002'
embed = OpenAIEmbeddings(
    model=model_name,
    openai_api_key="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"
)


data = ""

with open("app/temp.json",'r') as file: 
    data = json.load(file)

# print(data)

for i, (outer_key, inner_dict) in enumerate(tqdm(data.items())):
    print(f"Record {i + 1}")
    print(f"Outer Key: {outer_key}")

    for inner_key, inner_data in inner_dict.items():
        print(f"Inner Key: {inner_key}")
        itemp = "Issue_incident : {}_{}".format(outer_key,inner_key)
        print(itemp)
        # print(f"Spans: {inner_data['spans']}")
        # print(f"StackTrace: {inner_data['stackTrace']}")
        # print(f"IssueData: {inner_data['issueData']}")
        # print(f"Request Payload: {inner_data['request_payload']}")
        # print(f"Response Payload: {inner_data['response_payload']}")

    
