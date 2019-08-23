FROM python:3.7-slim-buster
LABEL MAINTAINER="Mikolaj Pawlikowski <mikolaj@pawlikowski.pl>"

WORKDIR /powerfulseal

RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

COPY Makefile LICENSE README.md setup.py /powerfulseal/
COPY powerfulseal/ /powerfulseal/powerfulseal/
RUN python -m pip --no-cache-dir install . && python -m pip list .

ENTRYPOINT ["python", "-m", "powerfulseal.cli.__main__"]
