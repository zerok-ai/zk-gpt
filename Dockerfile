FROM  python:3.8-slim

RUN mkdir -p /zk/app

COPY ./app /zk/app
WORKDIR /zk/app

ENV PYTHONPATH=/zk

RUN pip install -r requirements.txt

CMD ["python", "main.py"]