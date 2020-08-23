# our builder image
FROM python:3.7-slim-buster as builder

# install all the build dependencies
RUN apt-get update && \
    apt-get install -y build-essential curl libffi-dev libssl-dev && \
    apt-get clean && \
    apt-get autoclean && \
    apt-get autoremove

ARG http_proxy
ARG https_proxy
ARG no_proxy

# download kubectl
RUN if [ `uname -m` = "aarch64" ] ; then KUBECTL_ARCH="arm64"; else KUBECTL_ARCH="amd64"; fi \
    && curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.18.0/bin/linux/${KUBECTL_ARCH}/kubectl \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl \
    && kubectl version --client

# copy powerfulseal package
WORKDIR /powerfulseal
COPY Makefile LICENSE README.md setup.py setup.cfg MANIFEST.in /powerfulseal/
COPY powerfulseal/ /powerfulseal/powerfulseal/
COPY docs/ /powerfulseal/docs/

# install it with pip
RUN pip install . && pip list .


# the actual image we will be pushing up
FROM python:3.7-slim-buster
LABEL MAINTAINER="Mikolaj Pawlikowski <opensource@bloomberg.net>"

# copy over the site-packages from builder
COPY --from=builder /usr/local/lib/python3.7/site-packages /usr/local/lib/python3.7/site-packages
# also copy over the executable helpers
COPY --from=builder /usr/local/bin/powerfulseal /usr/local/bin/seal /usr/local/bin/
# copy over the kubectl command
COPY --from=builder /usr/local/bin/kubectl /usr/local/bin/kubectl
# list the installed packages and their versions
RUN pip list


ENTRYPOINT ["powerfulseal"]
