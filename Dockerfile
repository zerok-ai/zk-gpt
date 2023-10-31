FROM  python:3.8-slim-buster

COPY ./app /zk
WORKDIR /zk

RUN pip install -r requirements.txt

CMD ["python", "main.py"]