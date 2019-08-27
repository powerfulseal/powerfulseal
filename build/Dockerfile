FROM python:3.7-slim-buster
LABEL MAINTAINER="Mikolaj Pawlikowski <opensource@bloomberg.net>"

WORKDIR /powerfulseal

RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

COPY Makefile LICENSE README.md setup.py /powerfulseal/
COPY powerfulseal/ /powerfulseal/powerfulseal/
RUN pip --no-cache-dir install . && pip list .

ENTRYPOINT ["powerfulseal"]
