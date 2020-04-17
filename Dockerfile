FROM python:3
RUN apt-get update --fix-missing && apt-get install -y gdal-bin libgdal-dev postgis
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements/ /code/
RUN pip install -r local.txt
COPY . /code/
