FROM python:3.6-slim-buster

WORKDIR /app

RUN apt-get update \
  && apt-get -y install netcat postgresql

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .


CMD sh -c 'while ! nc -z flask_db 5432; do sleep 0.1; done && flask run --host=0.0.0.0'