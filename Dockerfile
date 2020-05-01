FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements/ /code/
RUN pip install -r production.txt
COPY . /code/
COPY entrypoint.sh /code/
# ENTRYPOINT ["/code/entrypoint.sh"]