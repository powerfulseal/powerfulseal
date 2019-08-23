FROM python:3.7-slim-buster
MAINTAINER Mikolaj Pawlikowski <mikolaj@pawlikowski.pl>

WORKDIR /powerfulseal

COPY powerfulseal Makefile LICENSE README.md setup.py /powerfulseal/
RUN pip install -e .

ENTRYPOINT ["powerfulseal"]