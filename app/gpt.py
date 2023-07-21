import openai
import config

openai.api_key = config.configuration.get("openai_key", "")


class GPTServiceProvider:
    gptHandlers = dict()

    def registerGPTHandler(self, handler):
        if handler not in self.gptHandlers:
            self.gptHandlers[handler] = GPT()
        return self.gptHandlers[handler]

    def deregisterGPTHandler(self, handler):
        if handler in self.gptHandlers:
            del self.gptHandlers[handler]

    def hasHandler(self, handler):
        return handler in self.gptHandlers


class GPT:
    context = []

    def setContext(self, contextText):
        self.context.append(
            {"role": "system", "content": contextText}
        )

    def findAnswers(self, question):
        self.context.append(
            {"role": "user", "content": question}
        )

        print(self.context)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=self.context
        )

        result = ''
        for choice in response.choices:
            result += choice.message.content

        self.context.append(
            {"role": "system", "content": result}
        )
        return result
