from langchain.prompts import PromptTemplate


class PromptFactory:
    # issue_summary = """You are a backend developer AI assistant. Your task is to figure out why an issue \
    # happened and present it in a concise manner wrt exception,latency,out of memory, service unreacable etc. The issue here is defined as {issue_prompt}.
    # We have collected {issue_data} and will feed them to you one by one. Come up with the \
    # likeliest cause based on the data presented to you. 
    # """

    exception_data = """You are a backend developer AI assistant.
    Your task is to figure out why an issue happened and present it in a concise manner.
    The issue's summary is here defined as {issue_data}. We have collected exceptions stack trace occured across spans as {exception_data}.
    Come up with the likeliest cause based on the exception data presented to you and brief the issue's exception stack trace if so. 
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

    final_summary_prompt = """As a backend developer AI assistant, your primary objective is to identify the root cause of an issue,
    summarize it, and provide a concise explanation. The issue's
    exception stack trace is summarized as {exception_summary}. Additionally,{trace_summary} \
    is a summary of the trace data collected for this issue, and {req_res_summary} \
    is the summary of the request-response payload pertaining to this issue,Your task is to determine \
    the most likely cause based on the provided summary data in 3 or 4 lines without leaving any key data points. in a saperate line highlight any anomalous data points if present as "anomalies".
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

    user_query_prompt = """ your key task is \
    to respond to the user's query, "{query}," by drawing upon both the system user context provided by \
    "{user_qna_context_data}" and the given issue summarized as {issue_summary} and relevant Pinecone similarity  \
    documents retrieved for the specific query, presented as "Documents: {pinecone_similarity_docs}.
    """

    prompt_infos = [
        # {
        #     'name': 'issue_summary',
        #     'description': 'Template to summarise the give issue',
        #     'prompt_template': issue_summary,
        #     "input_variables": ["issue_data", "issue_prompt"],
        #     "output_variables": "issue_summary"
        # },
        {
            'name': 'exception_data',
            'description': 'Template used to inference the issue using exception data',
            'prompt_template': exception_data,
            "input_variables": ["issue_data", "exception_data"],
            "output_variables": "exception_summary"
        },
        {
            'name': 'trace_data',
            'description': 'Template used to inference the issue using trace data',
            'prompt_template': trace_data,
            "input_variables": ["exception_summary", "trace_data"],
            "output_variables": "trace_summary"
        },
        {
            'name': 'request_response_payload',
            'description': 'Template used to inference the issue using request response data',
            'prompt_template': request_response_payload,
            "input_variables": ["trace_summary", "req_res_data"],
            "output_variables": "req_res_summary"
        },
        {
            'name': 'final summary',
            'description': 'Template used to inference the issue with final summary',
            'prompt_template': final_summary_prompt,
            "input_variables": ["exception_summary", "trace_summary", "req_res_summary"],
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
        #     'description': 'Template to check if the issue occurred due to CPU contraints',
        #     'prompt_template': cpu_usage_events_template
        # },
        # {
        #     'name': 'memory usage template',
        #     'description': 'Template to check if the issue occurred due to memory constraints',
        #     'prompt_template': memory_usage_events_template
        # },
        # {
        #     'name': 'pod events template',
        #     'description': 'Template to check if the incident occurred due to pod issue',
        #     'prompt_template': pod_k8s_events_template
        # },
        #  {
        #     'name': 'deployment template',
        #     'description': 'Template to check if the incident happened due to recent deployment',
        #     'prompt_template': deploy_k8s_events_template
        # },
        #  {
        #     'name': 'Config template',
        #     'description': 'Config map template ',
        #     'prompt_template': configmap_k8s_events_template
        # }
    ]

    user_query_prompt_infos = [
        {
            'name': 'User Query Prompt',
            'description': 'Template used to respond to the users query',
            'prompt_template': user_query_prompt,
            "input_variables": ["query", "pinecone_similarity_docs", "issue_summary", "user_qna_context_data"],
            "output_variables": "user_query_response"
        }
    ]

    def get_all_prompts(self):
        return self.prompt_infos

    def get_all_user_query_prompts(self):
        return self.user_query_prompt_infos

    def generate_prompts_for_sequential_chain(self):
        prompts = []
        output_keys = []

        prompt_templates = self.get_all_prompts()
        for prompt_tem in prompt_templates:
            prompt_template = PromptTemplate(input_variables=prompt_tem['input_variables'],
                                             template=prompt_tem['prompt_template'])
            prompts.append(prompt_template)
            output_keys.append(prompt_tem['output_variables'])
        return prompts, output_keys

    def generate_prompts_for_user_query_sequential_chain(self):
        prompts = []
        output_keys = []

        prompt_templates = self.get_all_user_query_prompts()
        for prompt_tem in prompt_templates:
            prompt_template = PromptTemplate(input_variables=prompt_tem['input_variables'],
                                             template=prompt_tem['prompt_template'])
            prompts.append(prompt_template)
            output_keys.append(prompt_tem['output_variables'])
        return prompts, output_keys
