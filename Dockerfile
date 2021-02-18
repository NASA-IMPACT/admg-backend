# pull official base image
FROM python:3.8.5 AS builder

# set work directory
WORKDIR /home/app/web

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update --fix-missing && apt-get install -y gdal-bin libgdal-dev postgis netcat

# lint
RUN pip install --upgrade pip
RUN pip install flake8
COPY . .

# install dependencies
COPY requirements/ .
RUN pip install -r local.txt

# run entrypoint.sh
ENTRYPOINT ["/home/app/web/entrypoint.sh"]
