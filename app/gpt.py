import openai

from app import config
from app.utils import zk_logger

openai.api_key = config.configuration.get("openai_key", "")
log_tag = "gpt_service_provider"
logger = zk_logger.logger

class GPTServiceProvider:
    gptHandlers = dict()

    def registerGPTHandler(self, handler):
        if handler not in self.gptHandlers:
            self.gptHandlers[handler] = GPT()
        logger.info(log_tag, "registerGPTHandler > " + handler + "[" + str(self.gptHandlers[handler].contextSize()) + "]")
        return self.gptHandlers[handler]

    def deregisterGPTHandler(self, handler):
        logger.info(log_tag, "deregisterGPTHandler < " + handler)
        if handler in self.gptHandlers:
            del self.gptHandlers[handler]

    def hasHandler(self, handler):
        logger.info(log_tag, "hasHandler | " + handler)
        return handler in self.gptHandlers


class GPT:
    context = []

    def contextSize(self):
        return len(self.context)

    def setContext(self, contextText):
        self.context.append(
            {"role": "system", "content": str(contextText)}
        )

    def findAnswers(self, question: str):
        self.context.append(
            {"role": "user", "content": question}
        )

        self.context = self.context[-50:]
        logger.info(log_tag, self.context)

        response = openai.ChatCompletion.create(
            # model="gpt-3.5-turbo",
            model="gpt-3.5-turbo-16k",
            messages=self.context,
        )

        result = ''
        for choice in response.choices:
            result += choice.message.content

        self.context.append(
            {"role": "system", "content": result}
        )
        return result
