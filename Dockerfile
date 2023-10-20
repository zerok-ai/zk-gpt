FROM --platform=linux/amd64 python:3.8-slim-buster

# base name of the executable
ENV exeBaseName="zk-gpt"

# full path to the all the executables
ENV exeAMD64="${exeBaseName}-amd64"
ENV exeARM64="${exeBaseName}-arm64"

COPY ./app /zk
WORKDIR /zk

COPY app-start.sh .
RUN chmod +x app-start.sh

RUN pip install -r requirements.txt

CMD ["sh","-c","./app-start.sh --amd64 ${exeAMD64} --arm64 ${exeARM64}"]
CMD ["python", "main.py"]