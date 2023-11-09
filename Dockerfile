# First stage: build the application
FROM python:3.9 as builder

RUN mkdir -p /zk/app

WORKDIR /zk

COPY ./app /zk/app

ENV PYTHONPATH=/zk

RUN pip install pyinstaller

RUN pip install -r app/requirements.txt

RUN pyinstaller app/main.py --target-arch arm64 --onefile --copy-metadata urllib3 --name zk-gpt-arm64 --collect-all=langchain --collect-all=pinecone --collect-all=langsmith --collect-all="tiktoken_ext" --collect-all=tiktoken --hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext
RUN pyinstaller app/main.py --target-arch amd64 --onefile --copy-metadata urllib3 --name zk-gpt-amd64 --collect-all=langchain --collect-all=pinecone --collect-all=langsmith --collect-all="tiktoken_ext" --collect-all=tiktoken --hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext


# Second stage: create the runtime image
FROM python:3.9-slim

WORKDIR /zk

# Copy the built application from the builder stage
COPY --from=builder /zk/dist /zk
COPY --from=builder /zk/app/requirements.txt /zk

# base name of the executable
ENV exeARM64="zk-gpt-arm64"
ENV exeAMD64="zk-gpt-amd64"

RUN pip install -r requirements.txt
# copy the start script
COPY app-start.sh .

RUN chmod +x app-start.sh
RUN chmod +x zk-gpt-arm64
RUN chmod +x zk-gpt-amd64

## call the start script
CMD ["sh","-c","./app-start.sh --amd64 ${exeAMD64} --arm64 ${exeARM64} -c config/config.yaml"]

