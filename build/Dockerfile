# our builder image
FROM python:3.7-slim-buster as builder

# install all the build dependencies
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

# copy powerfulseal package
WORKDIR /powerfulseal
COPY Makefile LICENSE README.md setup.py setup.cfg MANIFEST.in /powerfulseal/
COPY powerfulseal/ /powerfulseal/powerfulseal/

# install it with pip
RUN pip install . && pip list .


# the actual image we will be pushing up
FROM python:3.7-slim-buster
LABEL MAINTAINER="Mikolaj Pawlikowski <opensource@bloomberg.net>"

# copy over the site-packages from builder
COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
# also copy over the executable helpers
COPY --from=builder /usr/local/bin/powerfulseal /usr/local/bin/seal /usr/local/bin/
# list the installed packages and their versions
RUN pip list

ENTRYPOINT ["powerfulseal"]
