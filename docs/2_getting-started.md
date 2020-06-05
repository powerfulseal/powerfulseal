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

If you have a [`kubeconfig`](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file ready (for example in `~/.kube/config`) and working with `Kubernetes`, you can start the seal on defaults:

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
    interactive
```

To see how to use other modes, see our [docs on modes](./modes)


## Hello world!

Write the following hello world policy to `policy.yml`:

```yaml
scenarios:
- name: Hello chaos!
  description: >
    Verifies that after a pod is killed,
    it's succesfully rescheduled after 30 seconds.
  steps:
  # kill a kube-system pod
  - podAction:
      matches:
        - namespace: kube-system
      filters:
        - randomSample:
            size: 1
      actions:
        - kill:
            probability: 1
  - wait:
      seconds: 30
  # make sure all pods are running in the namespace
  - podAction:
      matches:
        - namespace: kube-system
      actions:
        - checkPodState:
            state: Running
```

You can then run the hello world policy in autonomus mode:

```sh
powerfulseal autonomous --policy-file ./policy.yaml
```

You will see an output similar to the following one. Note, that the Seal killed a pod, and then verified that it was successfuly restarted. By default, it will continue to run this experiment over and over, so feel free to press `Ctrl-C` to kill it.

```sh
$ powerfulseal autonomous --policy-file stuff/policy1.yml
2020-06-05 12:42:03 INFO __main__ verbosity: None; log level: INFO; handler level: INFO
2020-06-05 12:42:03 INFO __main__ Creating kubernetes client with config /Users/chaos/.kube/config (path found for backwards compatibility)
2020-06-05 12:42:03 INFO k8s_client Initializing with config: /Users/chaos/.kube/config
2020-06-05 12:42:03 INFO __main__ No cloud driver - some functionality disabled
2020-06-05 12:42:04 INFO __main__ Using stdout metrics collector
2020-06-05 12:42:04 INFO __main__ Starting the UI server (0.0.0.0:8000)
2020-06-05 12:42:04 INFO __main__ STARTING AUTONOMOUS MODE
2020-06-05 12:42:04 INFO scenario.Hello chaos! Starting scenario 'Hello chaos!' (3 steps)
2020-06-05 12:42:04 INFO action_nodes_pods.Hello chaos! Matching 'namespace' {'namespace': 'kube-system'}
2020-06-05 12:42:04 INFO action_nodes_pods.Hello chaos! Matched 37 pods in namespace kube-system
2020-06-05 12:42:04 INFO action_nodes_pods.Hello chaos! Filtered set length: 1
2020-06-05 12:42:04 INFO action_nodes_pods.Hello chaos! Pod killed: [pod #32 name=kube-state-metrics-7b4944dfbb-zrlrz namespace=kube-system containers=1 ...]
2020-06-05 12:42:04 INFO scenario.Hello chaos! Sleeping for 30 seconds
2020-06-05 12:42:34 INFO action_nodes_pods.Hello chaos! Matching 'namespace' {'namespace': 'kube-system'}
2020-06-05 12:42:35 INFO action_nodes_pods.Hello chaos! Matched 37 pods in namespace kube-system
2020-06-05 12:42:35 INFO action_nodes_pods.Hello chaos! Filtered set length: 37
2020-06-05 12:42:35 INFO scenario.Hello chaos! Scenario finished
```

We just verified experimentally, that the `Kubernetes` cluster was able to successfully restart a pod within 30 seconds. Now, what would happen if you changed the wait to 1 second?

```yaml
...
  - wait:
      seconds: 1
```

Most likely this:

```
...
2020-06-05 12:53:26 INFO action_nodes_pods.Hello chaos! Pod killed: [pod #14 name=kube-apiserver-metrics-pkh6n namespace=kube-system containers=1 ...]
2020-06-05 12:53:26 INFO scenario.Hello chaos! Sleeping for 1 seconds
2020-06-05 12:53:27 INFO action_nodes_pods.Hello chaos! Matching 'namespace' {'namespace': 'kube-system'}
2020-06-05 12:53:27 INFO action_nodes_pods.Hello chaos! Matched 37 pods in namespace kube-system
2020-06-05 12:53:27 INFO action_nodes_pods.Hello chaos! Initial set length: 37
2020-06-05 12:53:27 INFO action_nodes_pods.Hello chaos! Filtered set length: 37
2020-06-05 12:53:27 ERROR action_nodes_pods.Hello chaos! Expected pod in state 'Running', got 'ContainerCreating' ([pod #14 name=kube-apiserver-metrics-f98lw namespace=kube-system containers=1 ...])
2020-06-05 12:53:27 WARNING scenario.Hello chaos! Step returned failure {'podAction': {'matches': [{'namespace': 'kube-system'}], 'actions': [{'checkPodState': {'state': 'Running'}}]}}. Finishing scenario early
2020-06-05 12:53:27 ERROR policy_runner Exiting early
2020-06-05 12:53:27 ERROR __main__ Policy runner finishes with an error
```

OK, so that's a taste of what powerfulseal policies are capable of. Learn more about [policies here](./policies).

## Modes of operation

Powerfulseal supports multiple modes of operation.

[Learn about modes now](./modes){: .btn .btn-secondary .fs-5 .mb-4 .mb-md-0 .mr-2 }
