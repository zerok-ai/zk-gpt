FROM --platform=linux/arm64/v8 python:3.9
#RUN apt-get update
#RUN apt-get install binutils
#FROM python:3.9-slim
RUN mkdir -p /zk/app

WORKDIR /zk

COPY ./app /zk/app

# zk/app app folder got copied

# zk/dist/

ENV PYTHONPATH=/zk

RUN pip install pyinstaller

RUN pip install -r app/requirements.txt

RUN pyinstaller app/main.py --target-arch arm64 --onefile --name zk-gpt

#CMD ["python", "main.py"]

#COPY /dist/zk-gpt /zk/zk-gpt


#COPY ./app/requirements.txt /zk/

#COPY ./config/config.yaml /zk/app/config/config.yaml

# base name of the executable
ENV exeBaseName="zk-gpt"

## full path to the all the executables
#ENV exeGptAMD64="${exeBaseName}-amd64"
#ENV exeGptARM64="${exeBaseName}-arm64"
#
## copy the executables
#COPY *"bin/$exeAMD64" .
#COPY *"bin/$exeARM64" .

# copy the start script
COPY app-start.sh .
RUN chmod +x app-start.sh

COPY /dist/zk-gpt .

# call the start script
CMD ["sh","-c","./app-start.sh --arm64 ${exeBaseName} -c config/config.yaml"]

#CMD ["/zk/dist/zk-gpt"]




#ENV PYTHONPATH=/zk
#CMD ["python", "main.py"]