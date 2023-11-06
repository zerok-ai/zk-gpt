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


CMD ["/zk/dist/zk-gpt"]

#ENV PYTHONPATH=/zk
#CMD ["python", "main.py"]