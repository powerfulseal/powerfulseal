---
layout: default
title: Getting Started
nav_order: 2
description: ""
permalink: /getting-started
---

# Getting started
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Local installation

`PowerfulSeal` is available to install through [pip](https://pypi.org/project/powerfulseal/).

### Prerequisites

#### Python

You're going to need [`python`](https://www.python.org/downloads/) 3.7+.

```sh
python --version
Python 3.7.6
```

#### Setting up a virtualenv

Though optional, it is a good practice is to always use [virtualenv](https://virtualenv.pypa.io/en/stable/). You can create and activate one like this:

```sh
python -m virtualenv env
source env/bin/activate
```

### Installing through pip

Installing from [pip](https://pypi.org/project/powerfulseal/) is easy:

```sh
pip install powerfulseal
```

### Starting the Seal

To see the syntax of the commands, you can always run:

```sh
powerfulseal --help
```

If you have a [`kubeconfig`](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file ready (for example in `~/.kube/config`) and working with `kubernetes`, you can start the seal on defaults:

```sh
powerfulseal interactive
```

This will start a command line, interactive CLI, just like the following. You can type commands inside of it.

```sh
(seal) $
```

Try listing pods from the `kube-system` namespace:

```sh
(seal) $ pods kube-system
```

For help, just type `help`. For more information about the modes, see our [docs on modes](./modes).

## Running from Docker

### Download docker image

For each [release](https://github.com/bloomberg/powerfulseal/releases) a `docker` image is built and published to the [docker hub](https://hub.docker.com/_/powerfulseal).

```sh
docker pull store/bloomberg/powerfulseal:3.0.0
```

### Run docker image

You can use the `docker` image in a similar fashion to running locally. You will just need to pass it your `kubeconfig`.

Below is an example of using the `-v` flag to inject your local `kubeconfig` to the image (`-v ~/.kube:/root/.kube`)

```sh
docker run -it \
    -v ~/.kube:/root/.kube \
    docker.io/store/bloomberg/powerfulseal:2.8.0 \
        interactive --no-cloud --inventory-kubernetes
```

To see how to use other modes, see our [docs on modes](./modes)

## Modes of operation

You just learned how to start the interactive mode, but it's just a beginning. Powerfulseal supports multiple modes of operation.

[Learn about modes now](./modes){: .btn .btn-secondary .fs-5 .mb-4 .mb-md-0 .mr-2 }
