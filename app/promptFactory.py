from langchain.prompts import PromptTemplate


class PromptFactory:
    issue_summary = """You are a backend developer AI assistant. Your task is to figure out why an issue \
    happened and present it in a concise manner wrt exception,latency,out of memory, service unreacable etc. The issue here is defined as {issue_prompt}.
    We have collected {issue_data} and will feed them to you one by one. Come up with the \
    likeliest cause based on the data presented to you. 
    """

    exception_data = """You are a backend developer AI assistant.
    Your task is to figure out why an issue happened and present it in a concise manner.
    The issue's summary is here defined as {issue_summary}. We have collected exceptions occured across spans as {exception_data}.
    Come up with the likeliest cause based on the exception data presented to you and brief the issue is the exception stack trace if so. 
    """

    trace_data = """You are a backend developer AI assistant.
    Your task is to figure out why an issue happened and present it in a concise manner.
    The issue here is defined as {exception_summary}. We have collected spans data of the trace of the given issue  \
    and will feed them to you one by one as {trace_data}.
    Come up with the likeliest cause based on the spans data presented to you. and brief the sources and destinations and spans that are likely causing the issue.
    """

    request_response_payload = """You are a backend developer AI assistant.
    Your task is to figure out why an issue happened and present it in a concise manner.
    The issue's summary is here defined as {trace_summary}. We have collected request and response payload across all the spans of the trace of the given issue as {req_res_data}.
    Come up with the likeliest cause based on the request, response data presented to you brief the issue if there are any anolomy in the data. 
    """

    pod_k8s_events = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    deploy_k8s_events = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    configmap_k8s_events = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    cpu_usage_events = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    log_data = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    memory_usage_events = """<explain about before summary>
    {input} <brief about the current data> {custom_data}"""

    prompt_infos = [
        {
            'name': 'issue_summary',
            'description': 'Template to summarise the give issue',
            'prompt_template': issue_summary,
            "input_varaibles": ["issue_data", "issue_prompt"],
            "output_variables": "issue_summary"
        },
        {
            'name': 'exception_data',
            'description': 'Template used to inference the issue using exception data',
            'prompt_template': exception_data,
            "input_variables": ["exception_data"],
            "input_varaibles": ["issue_summary", "exception_data"],
            "output_variables": "exception_summary"
        },
        {
            'name': 'trace_data',
            'description': 'Template used to inference the issue using trace data',
            'prompt_template': trace_data,
            "input_varaibles": ["exception_summary", "trace_data"],
            "output_variables": "trace_summary"
        },
        {
            'name': 'request_response_payload',
            'description': 'Template used to inference the issue using request response data',
            'prompt_template': request_response_payload,
            "input_varaibles": ["trace_summary", "req_res_data"],
            "output_variables": "final_summary"
        }
        # ,
        # {
        #     'name': 'logs template',
        #     'description': 'Template used to inference the issue using log data',
        #     'prompt_template': log_data_template
        # },
        # {
        #     'name': 'Cpu usage template',
        #     'description': 'Template to check if the issue occured due to CPU contraints',
        #     'prompt_template': cpu_usage_events_template
        # },
        # {
        #     'name': 'memory usage template',
        #     'description': 'Template to check if the issue occured due to memory contraints',
        #     'prompt_template': memory_usage_events_template
        # },
        # {
        #     'name': 'pod events template',
        #     'description': 'Template to check if the incident occured due to pod issue',
        #     'prompt_template': pod_k8s_events_template
        # },
        #  {
        #     'name': 'deployemnt template',
        #     'description': 'Template to check if the incident happend due to recent deplpyment',
        #     'prompt_template': deploy_k8s_events_template
        # },
        #  {
        #     'name': 'Config template',
        #     'description': 'Config map template ',
        #     'prompt_template': configmap_k8s_events_template
        # }
    ]

    def getAllPrompts(self):
        return self.prompt_infos

    def generatePromptsForSequentialChain(self):
        print("")
        prompts = []
        output_keys = []

        prompt_templates = self.getAllPrompts()
        for prompt_tem in prompt_templates:
            prompt = prompt_tem['prompt_template']
            print("prompt : {}".format(prompt))
            prompt_template = PromptTemplate(input_variables=prompt_tem['input_varaibles'],
                                             template=prompt_tem['prompt_template'])
            prompts.append(prompt_template)
            output_keys.append(prompt_tem['output_variables'])
        return prompts, output_keys
