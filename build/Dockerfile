FROM python:3.7-slim-buster
LABEL MAINTAINER="Mikolaj Pawlikowski <mikolaj@pawlikowski.pl>"

WORKDIR /powerfulseal

RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

COPY powerfulseal Makefile LICENSE README.md setup.py /powerfulseal/
RUN pip install .

ENTRYPOINT ["powerfulseal"]