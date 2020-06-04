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

You're going to need [`python`](https://www.python.org/downloads/) 3.7+.

```sh
python --version
Python 3.7.6
```

#### Setting up a virtualenv

A good practice is to always use [virtualenv](https://virtualenv.pypa.io/en/stable/). You can create and activate one like this:

```sh
python -m virtualenv env
source env/bin/activate
```

### Installing through pip

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

This will start a command line, interactive CLI, just like the following:

```sh
$ powerfulseal interactive
(...)
(seal) $
```

Try listing pods from the `kube-system` namespace:

```sh
(seal) $ pods kube-system
```

For help, just type `help`. For more information about the modes, see our [docs on modes](/modes).

## Docker

The automatically built docker images are now available on [docker hub](https://hub.docker.com/_/powerfulseal)

```sh
docker pull bloomberg/powerfulseal:2.7.0
```