FROM python:3
RUN apt-get update --fix-missing && apt-get install -y gdal-bin libgdal-dev post
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements/ /code/
RUN pip install -r local.txt
RUN pip install -r production.txt
COPY . /code/
# COPY entrypoint.sh /code/
# ENTRYPOINT ["/code/entrypoint.sh"]