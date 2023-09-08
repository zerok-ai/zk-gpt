class PromptFactory():
    issue_summary_template = """An issue is defined as set of attributes separated by `¦` character. this convention is not to be part of summary the issue in this case is " + str(issueSummary["issue_title"]
        and attributes include kubernetes namespace/service name and the issue type
        We have collected " + str(issueSummary["total_count"]) data samples for inference of this issue.
        Data was collected from zeroK operator and kubernetes metrics server.
        To understand why a particular incident happened, click on any distinct incident on the right \

    Here is a question:
    {input}"""

    incident_rca_template = """You are a very smart Python programmer who writes unit tests using pytest. \
    You provide test functions written in pytest with asserts. \
    You explain the code in a detailed manner. \

    Here is a input on which you create a test:
    {input}"""
    
    trace_data_template = """You are a very smart Python programmer who writes unit tests using pytest. \
    You provide test functions written in pytest with asserts. \
    You explain the code in a detailed manner. \

    Here is a input on which you create a test:
    {input}"""

    exception_template = """You are a very smart Kotlin programmer. \
    You provide answers for algorithmic and computer science problems in Kotlin. \
    You explain the code in a detailed manner. \

    Here is a question:
    {input}"""

    request_response_payload_template = """You are a very smart Kotlin programmer who writes unit tests using JUnit 5. \
    You provide test functions written in JUnit 5 with JUnit asserts. \
    You explain the code in a detailed manner. \

    Here is a input on which you create a test:
    {input}"""

    pod_k8s_events_template = """You are a poet who replies to creative requests with poems in English. \
    You provide answers which are poems in the style of Lord Byron or Shakespeare. \

    Here is a question:
    {input}"""

    deploy_k8s_events_template = """You are a Wikipedia expert. \
    You answer common knowledge questions based on Wikipedia knowledge. \
    Your explanations are detailed and in plain English.

    Here is a question:
    {input}"""

    configmap_k8s_events_template = """You create a creator of images. \
    You provide graphic representations of answers using SVG images.

    Here is a question:
    {input}"""

    cpu_usage_events_template = """You are a UK or US legal expert. \
    You explain questions related to the UK or US legal systems in an accessible language \
    with a good number of examples.

    Here is a question:
    {input}"""

    log_data_template = """You are a UK or US legal expert. \
    You explain questions related to the UK or US legal systems in an accessible language \
    with a good number of examples.

    Here is a question:
    {input}"""

    memory_usage_events_template = """Your job is to fill the words in a sentence in which words seems to be missing.
    
    Here is the input:
    {input}"""

    python_programmer = 'python programmer'
    kotlin_programmer = 'kotlin programmer'

    

    prompt_infos = [
        {
            'name': 'issue summary',
            'description': 'Template to summarise the give issue',
            'prompt_template': issue_summary_template
        },
        {
            'name': 'trace data',
            'description': 'Template used to inference the issue using trace data',
            'prompt_template': trace_data_template
        },
        {
            'name': 'exception template',
            'description': 'Template used to inference the issue using exception data',
            'prompt_template': exception_template
        },
        {
            'name': 'request response template',
            'description': 'Template used to inference the issue using request response data',
            'prompt_template': request_response_payload_template
        },
        {
            'name': 'logs template',
            'description': 'Template used to inference the issue using log data',
            'prompt_template': log_data_template
        },
        {
            'name': 'Cpu usage template',
            'description': 'Template to check if the issue occured due to CPU contraints',
            'prompt_template': cpu_usage_events_template
        },
        {
            'name': 'memory usage template',
            'description': 'Template to check if the issue occured due to memory contraints',
            'prompt_template': memory_usage_events_template
        },
        {
            'name': 'pod events template',
            'description': 'Template to check if the incident occured due to pod issue',
            'prompt_template': pod_k8s_events_template
        },
         {
            'name': 'deployemnt template',
            'description': 'Template to check if the incident happend due to recent deplpyment',
            'prompt_template': deploy_k8s_events_template
        },
         {
            'name': 'Config template',
            'description': 'Config map template ',
            'prompt_template': configmap_k8s_events_template
        }
    ]


    def getAllPrompts(self):
        return self.prompt_infos
    

    def createGtpContextUsingTemplate(self,dict): 
        return ""
    

