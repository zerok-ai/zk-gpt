import client
import gptLangchianInference
import pineconeInteraction
import slack_integration
from clientServices import postgresClient
from datetime import datetime

langChainInferenceProvider = gptLangchianInference.LangChainInference()
pineconeInteractionProvider = pineconeInteraction.PineconeInteraction()


def generate_and_store_inference(issue_id, incident_id):
    # getting langchain inferences
    issue_summary = client.getIssueSummary(issue_id)
    custom_data, langchain_inference = get_langchain_inference(issue_id, incident_id, issue_summary)
    inference = langchain_inference['final_summary']

    # vectorize data and push to pinecone
    vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchain_inference, custom_data)

    issue_title = issue_summary['issue_title']
    issue_last_seen = get_time_stamp_from_datatime(issue_summary['last_seen'])
    issue_first_seen = get_time_stamp_from_datatime(issue_summary['first_seen'])

    # store in DB
    postgresClient.insert_or_update_inference_to_db(issue_id, incident_id, inference, issue_title, issue_last_seen,
                                                    issue_first_seen)

    print(f"stored inference in DB for issue: {issue_id} and incidentId: {incident_id}")
    # slack integration
    slack_integration.store_inference_for_reporting(issue_id, incident_id, issue_last_seen)

    return inference


def generate_and_store_inference_for_scheduler(issue_id, incident_id, issue_data):
    issue_last_seen = get_time_stamp_from_datatime(issue_data["last_seen"])
    issue_first_seen = get_time_stamp_from_datatime(issue_data["first_seen"])

    print(f"last seen: {str(issue_last_seen)}")

    # getting langchain inferences
    issue_summary = client.getIssueSummary(issue_id)

    custom_data, langchain_inference = get_langchain_inference(issue_id, incident_id, issue_summary)

    inference = langchain_inference['final_summary']

    # vectorize data and push to pinecone
    vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchain_inference, custom_data)

    issue_title = issue_summary['issue_title']

    print(f"inference genereted succesfully for {issue_id} and now we are storign in DB")

    # store in DB
    postgresClient.insert_or_update_inference_to_db(issue_id, incident_id, inference, issue_title, issue_last_seen,
                                                    issue_first_seen)

    print(f"stored inference in DB for issue: {issue_id} and incidentId: {incident_id}")
    # slack integration
    slack_integration.store_inference_for_reporting(issue_id, incident_id, issue_last_seen)

    return inference


def get_langchain_inference(issue_id, incident_id, issue_summary):
    # fetch all the data required for langchain inference
    print("starting langchain inference: ")
    spans_map = client.getSpansMap(issue_id, incident_id)
    exception_map = []
    req_res_payload_map = []
    for span_id in spans_map:
        span_raw_data = client.getSpanRawdata(issue_id, incident_id, span_id)
        spans_map[span_id].update(span_raw_data)

    filtered_spans_map = dict()
    for spanId in spans_map:
        # remove error key from spanMap
        del spans_map[spanId]["error"]

        span = spans_map[spanId]
        span["span_id"] = spanId
        # remove exception span from spanMap
        if str(span["protocol"]).upper() == "EXCEPTION" or str(span["path"]).upper() == "/EXCEPTION":
            parent_span_id = span["parent_span_id"]
            exception_map.append(span["req_body"])
            if parent_span_id in spans_map:
                spans_map[parent_span_id]["exception"] = span["req_body"]
                filtered_spans_map[parent_span_id] = spans_map[parent_span_id]
        else:
            filtered_spans_map[spanId] = span

    for spanId in filtered_spans_map:
        span = spans_map[spanId]
        req_res_payload_map.append({"request_payload": span['req_body'], "span": spanId})
        req_res_payload_map.append({"response_payload": span['resp_body'], "span": spanId})

    # create input variable for langchain
    custom_data = {"issue_data": str(issue_summary["issue_title"]), "trace_data": str(filtered_spans_map),
                   "exception_data": str(exception_map), "req_res_data": str(req_res_payload_map),
                   "issue_prompt": "You are a backend developer AI assistant. Your task is to figure out why an issue happened based the exception,trace,request respone payload data's presented to you in langchain sequential chain manner, and present it in a concise manner."}

    # get langchain inference
    langchain_inference = langChainInferenceProvider.get_gpt_langchain_inference(issue_id, incident_id, custom_data)

    return custom_data, langchain_inference


def vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchian_inference, custom_data):
    # push data to pinecone
    pinecone_issue_data = dict()
    pinecone_issue_data['issue_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id, "data",
                                                                                         "issue",
                                                                                         custom_data['issue_data'],
                                                                                         "default", "default")
    pinecone_issue_data['trace_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id, "data",
                                                                                         "trace",
                                                                                         custom_data['trace_data'],
                                                                                         "default", "default")
    pinecone_issue_data['exception_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                             "data",
                                                                                             "exception",
                                                                                             custom_data[
                                                                                                 'exception_data'],
                                                                                             "default", "default")
    pinecone_issue_data['req_res_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                           "data",
                                                                                           "req_res",
                                                                                           custom_data['req_res_data'],
                                                                                           "default", "default")
    pinecone_issue_data['req_res_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                              "summary", "req_res",
                                                                                              langchian_inference[
                                                                                                  'req_res_summary'],
                                                                                              "default",
                                                                                              "default")
    pinecone_issue_data['final_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                            "summary", "final",
                                                                                            langchian_inference[
                                                                                                'final_summary'],
                                                                                            "default",
                                                                                            "default")
    pinecone_issue_data['exception_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                                "summary", "exception",
                                                                                                langchian_inference[
                                                                                                    'exception_summary'],
                                                                                                "default", "default")
    pinecone_issue_data['trace_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                            "summary", "trace",
                                                                                            langchian_inference[
                                                                                                'trace_summary'],
                                                                                            "default",
                                                                                            "default")
    # pinecone_issue_data['issue_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
    #                                                                                     "summary", "issue",
    #                                                                                     langchian_inference[
    #                                                                                         'issue_summary'], "default",
    #                                                                                     "default")
    data_list = [value for value in pinecone_issue_data.values()]
    pineconeInteractionProvider.vectorize_data_and_pushto_pinecone_db(issue_id, incident_id, data_list)


def get_time_stamp_from_datatime(date_time_str):
    if date_time_str is None:
        print("dateTimeString is NONE")
        raise Exception("invalid date time string")
    print("extracting time stamp")
    timestamp_str = date_time_str
    timestamp_dt = datetime.fromisoformat(timestamp_str)
    timestamp_pg = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    print("extracted time stamp")
    return timestamp_pg
