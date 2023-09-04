from prometheus_api_client import PrometheusConnect
from prometheus_api_client.utils import parse_datetime
from datetime import timedelta,datetime
import json
import threading
import concurrent.futures
prom = PrometheusConnect(url="http://127.0.0.1:9090", disable_ssl=True)

# Function to perform each Prometheus query
def perform_query(query, result_container, query_name):
    result = prom.custom_query(query=query)
    result_container[query_name] = result

def get_pod_information(namespace,pod,timestamp_str):
    print("Fetching Pod Information for pod: {} in namespace : {} \n".format(pod,namespace))
    response = {
        "pod_info": {},
        "container_info": []
    }
    try:
    # pod_join_query_format = 'kube_pod_info{namespace="%s",pod=~"%s"} * on(uid) group_left() kube_pod_created{namespace="%s",pod=~"%s"} * on(uid) group_left(image,image_id,image_spec,container,container_id) kube_pod_container_info{namespace="%s",pod=~"%s"}' % (namespace,pod, namespace,pod,namespace,pod)
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        timestamp = round(timestamp_datetime.timestamp())

        pod_info_query_1 = f'kube_pod_info{{namespace="{namespace}",pod=~"{pod}"}} @ {timestamp}'
        pod_info_query_2 = f'kube_pod_created{{namespace="{namespace}",pod=~"{pod}"}} @ {timestamp} '
        pod_info_query_3 = f'kube_pod_container_info{{namespace="{namespace}",pod=~"{pod}"}} @ {timestamp}'

        # Create an empty dictionary to store results
        results = {}

        # Create threads for each query, passing the query name as well
        thread1 = threading.Thread(target=perform_query, args=(pod_info_query_1, results, "result1"))
        thread2 = threading.Thread(target=perform_query, args=(pod_info_query_2, results, "result2"))
        thread3 = threading.Thread(target=perform_query, args=(pod_info_query_3, results, "result3"))

        # Start the threads
        thread1.start()
        thread2.start()
        thread3.start()

        # Wait for all threads to finish
        thread1.join()
        thread2.join()
        thread3.join()

        # Extract the results from the dictionary
        result1 = results.get("result1")
        result2 = results.get("result2")
        result3 = results.get("result3")

        result1 = prom.custom_query(query=pod_info_query_1)
        result2 = prom.custom_query(query=pod_info_query_2)
        result3 = prom.custom_query(query=pod_info_query_3)

        pod_info_data = result1[0]
        pod_creation_data = result2[0]
        response["pod_info"] = pod_info_data["metric"]
        response["pod_info"]['created_timestamp'] = pod_creation_data['value'][1]


        for container_info in result3:
            container_metadata = {
                "metadata": {
                    "created_timestamp": container_info['value'][0],
                    "status": int(container_info['value'][1])
                }
            }
            container_metadata["metadata"].update(container_info['metric'])
            response["container_info"].append(container_metadata)
            
        return response
    
    except Exception as e: 
         print("\n Exception Occured while calculated Pod metadata for pod: {} in namespace : {} as : {}".format(pod,namespace,e))

def getZkPodInferences(namespace,pod,timestamp_str):
    response = {
        "podName" : "podName",
        "metadata" : {},
        "zkInferences" : "zkInferences",
        "cpuUsage" : "cpuUsage",
        "memUsage" : "memUsage"
    }
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit the tasks for concurrent execution
            pod_info_future = executor.submit(get_pod_information, namespace, pod, timestamp_str)
            cpu_usage_future = executor.submit(get_cpu_usage, namespace, pod, timestamp_str)
            mem_usage_future = executor.submit(get_memory_usage, namespace, pod, timestamp_str)
            
            # Wait for all tasks to complete
            concurrent.futures.wait([pod_info_future, cpu_usage_future, mem_usage_future])
            
            # Retrieve and update the response data
            pod_information = pod_info_future.result()
            response["podName"] = pod_information['pod_info']['pod']
            response["cpuUsage"] = cpu_usage_future.result()
            response["memUsage"] = mem_usage_future.result()
            response["metadata"] = pod_information

            return json.dumps(response)
    except Exception as e: 
        print("\n Exception Occurred while calculating Zk Prometheus inferences for pod: {} in namespace: {} as: {}".format(pod, namespace, e))

def get_cpu_usage(namespace,pod,timestamp_str):
    print("CPU usage Calculation for for pod: {} in namespace : {} \n".format(pod,namespace))
    interval = "30s"
    rate_interval = "3m"  # This is the $__rate_interval value, you can adjust it as needed
    max_data_points = 820
    cpu_success_response_data = {
        "title": "CPU Usage",
        "success": True,
        "frames": []
    }
    cpu_failed_response_data = {
        "title": "CPU Usage",
        "success": False,
        "frames": []  
    }
    # Fetch the data for the query
    try:
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        from_time = timestamp_datetime - timedelta(minutes=10)
        to_time = timestamp_datetime + timedelta(minutes=10)
        query = f'sum(rate(container_cpu_usage_seconds_total{{namespace="{namespace}", pod=~"{pod}", image!="", container!=""}}[{rate_interval}])) by (container)'
        result = prom.custom_query_range(query=query, start_time=from_time, end_time=to_time, step=interval)
        for item in result:
            container_name = item['metric']['container']
            timestamps = [int(value[0] * 1000) for value in item['values']]
            values = [float(value[1]) for value in item['values']]
            frame = {
                "schema": {
                    "name": container_name
                },
                "data": {
                    "timeStamp": timestamps,
                    "values": values
                }
            }
            cpu_success_response_data["frames"].append(frame)
        return cpu_success_response_data
    except Exception as e:
        print("\n Exception Occured while calculated cpu usage for pod: {} in namespace : {} as : {}".format(pod,namespace,e))
        return cpu_failed_response_data

def get_memory_usage(namespace,pod,timestamp_str):
    print("Memory usage Calculation for for pod: {} in namespace : {} \n".format(pod,namespace))
    mem_success_response_data = {
        "title": "Memory Usage",
        "success": True,
        "frames": []
    }
    mem_failed_response_data = {
        "title": "CPU Usage",
        "success": False,
        "frames": []  
    }

    try:
        query = f'sum(container_memory_working_set_bytes{{namespace="{namespace}", pod=~"{pod}", image!="", container!=""}}) by (container)'
        # Define the time range
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        from_time = timestamp_datetime - timedelta(minutes=10)
        to_time = timestamp_datetime + timedelta(minutes=10)
        # Execute the query
        result = prom.custom_query_range(query=query, start_time=from_time, end_time=to_time, step=300)

        # Create frames based on the request data
        for item in result:
            container_name = item['metric']['container']
            timestamps = [int(value[0] * 1000) for value in item['values']]
            values = [int(value[1]) for value in item['values']]

            frame = {
                "schema": {
                    "name": container_name
                },
                "data": {
                    "values": [timestamps, values]
                }
            }
            mem_success_response_data["frames"].append(frame)
        return mem_success_response_data
    except Exception as e:
        print("\n Exception Occured while calculated memory usage for pod: {} in namespace : {} as : {}".format(pod,namespace,e))
        return mem_failed_response_data

def get_pod_status(namespace,pod,timestamp_str):
    timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
    timestamp = round(timestamp_datetime.timestamp())
    print("Fetching Pod Status for pod: {} in namespace : {} \n".format(pod,namespace))
    pod_status_query = "kube_pod_container_status_ready{namespace='%s',pod=~'%s'} @ %s" % (namespace,pod, timestamp)
    pod_result = prom.custom_query(query=pod_status_query)
    print(pod_result)
    if len(pod_result) > 0:
        pod_inference = pod_result[0]
        metric ,value = pod_inference.items()
        pod_info_dict = {}
        if len(metric) > 0 :
            for key, value in metric[1].items():
                pod_info_dict[key]=value
            return pod_info_dict

def get_pod_restart_count(namespace,pod,timestamp_str):
    
    print("Fetching Pod Restart Count for pod: {} in namespace : {} \n".format(pod,namespace))
    rs_success_response_data = {
        "title": "Restart Count Wrt Time Stamp",
        "success": True,
        "frames": []
    }
    rs_failed_response_data = {
        "title": "Restart Count Wrt Time Stamp",
        "success": False,
        "frames": []  
    }
    try:
        query = f'kube_pod_container_status_restarts_total{{namespace="{namespace}", pod=~"{pod}"}}'
        # Define the time range
        timestamp_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
        from_time = timestamp_datetime - timedelta(minutes=5)
        to_time = timestamp_datetime + timedelta(minutes=5)
        # Query Prometheus data for the restart events within the specified time range
        result = prom.custom_query_range(query=query, start_time=from_time, end_time=to_time, step=60)
        # if len(result) >1 : 
        #     result = result[0]
        # Extract relevant data from the request and populate the response frames
        print(result)
        for item in result:
            pod_name = item['metric']['pod']
            timestamps = [int(value[0] * 1000) for value in item['values']]
            restart_counts = [int(value[1]) for value in item['values']]

            frame = {
                "schema": {
                    "name": pod_name
                },
                "data": {
                    "values": [timestamps, restart_counts]
                }
            }
            rs_success_response_data["restartCount"]["frames"].append(frame)
        print(rs_success_response_data)
        return rs_success_response_data
    except Exception as e:
        print("\n Exception Occured while calculated Restart Count for pod: {} in namespace : {} as : {}".format(pod,namespace,e))
        return rs_failed_response_data

finalResponse = getZkPodInferences('zk-client','zk-operator.*','2023-09-01 09:05:00.000000')


print("\n -----------------------------------------------------------------------------------------------\n")
print(finalResponse)