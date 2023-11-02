from langchain.chains import SequentialChain

from app.internal.langchain_adapter import langchian_multi_chain_factory
from app.internal.langchain_adapter import prompt_factory
from app.utils import zk_logger

log_tag = "langchain_adapter"
logger = zk_logger.logger


class LangchainAdapter:
    def __init__(self):
        self.prompt_factory_instance = prompt_factory.PromptFactory()
        self.langchain_multi_chain_fact = langchian_multi_chain_factory.LangChainMultichainFactory()

    def get_gpt_langchain_inference(self, issue_id, incident_id, custom_data):
        try:
            logger.info(log_tag, "Inferencing the issue data using langchain for issue id : {} and incident id: {} \n".format(issue_id,
                                                                                                               incident_id))  # modify the print statement
            prompts, output_keys = self.prompt_factory_instance.generate_prompts_for_sequential_chain()

            sequential_list_chains = self.langchain_multi_chain_fact.get_sequential_chains(prompts, output_keys)

            overall_chain = SequentialChain(chains=sequential_list_chains, verbose=True,
                                            input_variables=["issue_prompt", "issue_data", "trace_data",
                                                             "exception_data", "req_res_data"],
                                            output_variables=["trace_summary", "exception_summary", "req_res_summary",
                                                              "final_summary"])

            final_issue_inference = overall_chain(custom_data)
            return final_issue_inference
        except Exception as e:
            logger.error(log_tag, f"An error occurred: {e}")
            return ""

    def get_user_query_gpt_langchain_inference(self, issue_id, incident_id, custom_data):
        try:
            logger.info(log_tag, "Answering the user query for the for issue id : {} and incident id: {} using langchain\n".format(
                issue_id,
                incident_id))

            prompts, output_keys = self.prompt_factory_instance.generate_prompts_for_user_query_sequential_chain()

            user_query_sequential_list_chains = self.langchain_multi_chain_fact.get_sequential_chains(prompts,
                                                                                                      output_keys)

            overall_chain = SequentialChain(chains=user_query_sequential_list_chains, verbose=True,
                                            input_variables=["query", "trace_data", "exception_data",
                                                             "request_response_payload"],
                                            output_variables=["user_query_response"])

            user_query_final_inference = overall_chain(custom_data)

            return user_query_final_inference
        except Exception as e:
            logger.error(log_tag, f"An error occurred: {e}")
            return ""
