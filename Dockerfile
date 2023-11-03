FROM  python:3.9-slim

#FROM python:3.9-slim

WORKDIR /zk

COPY ./app/requirements.txt /zk/
COPY ./dist/zk-gpt /zk/zk-gpt
COPY ./config/config.yaml /zk/config/config.yaml

RUN pip install -r requirements.txt

CMD ["uname -m"]

CMD ["/zk/zk-gpt"]

#ENV PYTHONPATH=/zk
#CMD ["python", "main.py"]