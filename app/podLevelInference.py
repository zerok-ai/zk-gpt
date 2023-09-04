from flask import jsonify
import client
import getPrometheusData
import datetime
import concurrent.futures

def getPrometheusData(issue_id, incident_id):
    spansMap = client.getSpansMap(issue_id, incident_id)
    source_destination_set = {}
    source_timestamp_dict = {}
    dest_timestamp_dict = {}
     # get all the sources and destinations
    for spanId in spansMap:
        span = spansMap[spanId]
        span["span_id"] = spanId
        source = span['source']
        destination = span['destination']
        source_timestamp_dict[source]=span['start_time']
        dest_timestamp_dict[destination] = span['start_time']
        if source is not None:
            source_destination_set.add(source)
        if destination is not None:
            source_destination_set.add(destination)
    # get all namespace and pods from the sources and destiantions
    namespace_service_list = []
    for pod in source_destination_set:
        namespace_service = pod.split('/')
        namespace = namespace_service[0]
        pod_prefix_regex = namespace_service[1][:5] + ".*"
        timestamp = source_timestamp_dict[pod] if pod in source_timestamp_dict else dest_timestamp_dict[pod]
        namespace_service_dict = {
            "namespace": namespace,
            "pod_prefix_regex": pod_prefix_regex,
            "timestamp": timestamp if timestamp is not None else datetime.time()
        }
        namespace_service_list.append(namespace_service_dict)

    # iterate over each pod and get pod information 
    pod_inference_list = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for podInfo in namespace_service_list:
            future = executor.submit(get_prometheus_data, podInfo["namespace"], podInfo["pod_prefix_regex"], podInfo['timestamp'])
            futures.append(future)
        for future in concurrent.futures.as_completed(futures):
            pod_inference = future.result()
            pod_inference_list.append(pod_inference)
    return pod_inference_list
    # pod_inference_list = []
    # for podInfo in namespace_service_list:
    #     podInference = getPrometheusData.getPodInferences(podInfo["namespace"],podInfo["pod_prefix_regex"],podInfo['timestamp'])
    #     pod_inference_list.append(podInference)
    
    # return pod_inference_list

def get_prometheus_data(namespace, pod_prefix_regex, timestamp):
    return getPrometheusData.get_prometheus_data(namespace, pod_prefix_regex, timestamp)


    










