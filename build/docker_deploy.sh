#!/bin/sh

docker login -u "$DOCKER_USER" -p "$DOCKER_PASSWORD" \
    && cd .. \
    && make tag \
    && make push
