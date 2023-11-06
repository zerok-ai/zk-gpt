# First stage: build the application
FROM python:3.9 as builder

RUN mkdir -p /zk/app

WORKDIR /zk

COPY ./app /zk/app

ENV PYTHONPATH=/zk

RUN pip install pyinstaller

RUN pip install -r app/requirements.txt

RUN pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt-arm64
RUN pyinstaller app/main.py --target-arch amd64 --onefile --name zk-gpt-amd64


# Second stage: create the runtime image
FROM python:3.9-slim

WORKDIR /zk/zk-gpt

# Copy the built application from the builder stage
COPY --from=builder /zk/dist /zk/zk-gpt

# base name of the executable
ENV exeARM64="zk-gpt-arm64"
ENV exeAMD64="zk-gpt-amd64"

# copy the start script
COPY app-start.sh .
RUN chmod +x app-start.sh

## call the start script
CMD ["sh","-c","./app-start.sh --amd64 ${exeAMD64} --arm64 ${exeARM64} -c config/config.yaml"]

