from langchain.chains import SequentialChain

import langchianMultiChainFactory
import promptFactory


class LangChainInference:
    def __init__(self):
        self.promptFactInstance = promptFactory.PromptFactory()
        self.langchianMultiChainFact = langchianMultiChainFactory.LangChainMultichainFactory()

    def get_gpt_langchain_inference(self, issue_id, incident_id, custom_data):
        try:
            print("Inferencing the issue data using langchain for issue id : {} and incident id: {} \n".format(issue_id,
                                                                                                               incident_id))  # modify the print statement
            prompts, output_keys = self.promptFactInstance.generate_prompts_for_sequential_chain()

            sequential_list_chains = self.langchianMultiChainFact.getSequentialChains(prompts, output_keys)

            overall_chain = SequentialChain(chains=sequential_list_chains, verbose=True,
                                            input_variables=["issue_prompt", "issue_data", "trace_data",
                                                             "exception_data", "req_res_data"],
                                            output_variables=["trace_summary", "exception_summary", "req_res_summary",
                                                              "final_summary"])

            final_issue_inference = overall_chain(custom_data)
            return final_issue_inference
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""

    def get_user_query_gpt_langchain_inference(self, issue_id, incident_id, custom_data):
        try:
            print("Answering the user query for the for issue id : {} and incident id: {} using langchain\n".format(
                issue_id,
                incident_id))

            prompts, output_keys = self.promptFactInstance.generate_prompts_for_user_query_sequential_chain()

            user_query_sequential_list_chains = self.langchianMultiChainFact.getSequentialChains(prompts, output_keys)

            overall_chain = SequentialChain(chains=user_query_sequential_list_chains, verbose=True,
                                            input_variables=["query", "trace_data", "exception_data", "request_response_payload"],
                                            output_variables=["user_query_response"])

            user_query_final_inference = overall_chain(custom_data)

            return user_query_final_inference
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""
