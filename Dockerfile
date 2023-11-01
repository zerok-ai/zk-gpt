FROM --platform=linux/amd64 python:3.9

COPY ./app /zk/app
WORKDIR /zk/app
ENV PYTHONPATH=/zk

RUN pip install -r requirements.txt

CMD ["python", "main.py"]