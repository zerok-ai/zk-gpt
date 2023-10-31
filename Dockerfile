FROM --platform=linux/amd64 python:3.9

COPY ./app /app
WORKDIR /app
ENV PYTHONPATH=/app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]