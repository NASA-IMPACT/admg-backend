# pull official base image
FROM python:3.8.5 AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements/ .
RUN pip install -r local.txt

COPY . /code/

RUN apt-get update --fix-missing && apt-get install -y gdal-bin libgdal-dev postgis netcat

# run entrypoint.sh
ENTRYPOINT [ "/code/entrypoint.sh" ]
