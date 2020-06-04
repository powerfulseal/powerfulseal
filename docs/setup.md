---
layout: default
title: Setup
nav_order: 4
description: ""
permalink: /setup
has_children: true
---

# Setup Powerfulseal
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

The setup depends on whether you run `PowerfulSeal` inside or outside of your cluster.


## Running inside of the cluster

If you're running inside of the cluster (for example from [the docker image](https://github.com/bloomberg/powerfulseal/tree/master/build)), the setup is pretty easy.

You can see an example of how to do it [in ./kubernetes](https://github.com/bloomberg/powerfulseal/tree/master/kubernetes). The setup involves:

- creating [RBAC rules](https://github.com/bloomberg/powerfulseal/blob/master/kubernetes/rbac.yml) to allow the seal to list, get and delete pods,
- creating a [powerfulseal configmap and deployment](https://github.com/bloomberg/powerfulseal/blob/master/kubernetes/powerfulseal.yml)
  - your scenarios will live in the configmap
  - if you'd like to use the UI, you'll probably also need a service and ingress
  - make sure to use `--use-pod-delete-instead-of-ssh-kill` flag to not need to configure SSH access for killing pods
- profit!
  - the Seal will self-discover the way to connect to `kubernetes` and start executing your policy


## Running outside of the cluster

If you're running outside of your cluster, the setup will involve:

- pointing PowerfulSeal at your Kubernetes cluster by giving it a Kubernetes config file
- pointing PowerfulSeal at your cloud by specifying the cloud driver to use and providing credentials
- making sure the seal can SSH into the nodes in order to execute `docker kill` command
- writing a set of policies

It should look something like [this](https://github.com/bloomberg/powerfulseal/blob/master/media/setup.png).


## Minikube setup

It is possible to test a subset of Seal's functionality using a [`minikube`](https://kubernetes.io/docs/setup/minikube/) setup.

To achieve that, please inspect the [Makefile](https://github.com/bloomberg/powerfulseal/blob/master/Makefile). You will need to override the ssh host, specify the correct username and use minikube's ssh keys.


If you'd like to test out the interactive mode, start with this:

```sh
seal \
  -vv \
  interactive \
    --no-cloud \
    --inventory-kubernetes \
    --ssh-allow-missing-host-keys \
    --remote-user docker \
    --ssh-path-to-private-key `minikube ssh-key` \
    --ssh-password `minikube ssh-password` \
    --override-ssh-host `minikube ip`
```

For label mode, try something like this:

```sh
seal \
  -vv \
  label \
    --no-cloud \
    --min-seconds-between-runs 3 \
    --max-seconds-between-runs 10 \
    --inventory-kubernetes \
    --ssh-allow-missing-host-keys \
    --remote-user docker \
    --ssh-path-to-private-key `minikube ssh-key` \
    --ssh-password `minikube ssh-password` \
    --override-ssh-host `minikube ip`
```

For autonomous mode, this should get you started:

```sh
seal \
  -vv \
  autonomous \
    --no-cloud \
    --policy-file ./examples/policy_kill_random_default.yml \
    --inventory-kubernetes \
    --prometheus-collector \
    --prometheus-host 0.0.0.0 \
    --prometheus-port 9999 \
    --ssh-allow-missing-host-keys \
    --remote-user docker \
    --ssh-path-to-private-key `minikube ssh-key` \
    --ssh-password `minikube ssh-password` \
    --override-ssh-host `minikube ip` \
    --host 0.0.0.0 \
    --port 30100
```