---
layout: default
title: Setup
nav_order: 5
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

`PowerfulSeal` has two main modes of operation: through `Kubernetes` or through `SSH`.

`Kubernetes` mode is the default, and it's easier to use. It kills pods by deleting them through the API.

`SSH` works by SSH-ing into the machine itself and executing command like `docker kill <pod ip>`. The pods then show as crashing. Unfortunately, it requires `SSH` access to all machines you're going to be doing chaos on, which is sometimes troublesome.


## Running on Kubernetes

Running on `Kubernetes` is easy. You can do that by:

- creating [RBAC rules](https://github.com/bloomberg/powerfulseal/blob/master/kubernetes/rbac.yml) to allow the seal to list, get and delete pods and nodes,
  - you might need to adjust it depending on what you are planning to do with the Seal
- creating a [configmap and deployment](https://github.com/bloomberg/powerfulseal/blob/master/kubernetes/powerfulseal.yml)
  - your scenarios will live in the configmap
  - if you'd like to use the UI, you'll probably also need a service and ingress

That's it. The Seal will self-discover the way to connect to `Kubernetes` and start executing your policy


## Running outside of the cluster

If you're running outside of your cluster, the setup will involve:

- pointing PowerfulSeal at your Kubernetes cluster by giving it a Kubernetes config file
- pointing PowerfulSeal at your cloud by specifying the cloud driver to use and providing credentials
- making sure the Seal can `SSH` into the nodes in order to execute `docker kill` command
- writing a set of policies

It should look something like [this](https://github.com/bloomberg/powerfulseal/blob/master/docs/media/setup.png).


## Minikube

It's easy to use `minikube` with the Seal. It should run well on the default settings. If you choose to use SSH access, you're going to need these options:

```sh
--ssh-allow-missing-host-keys \
--remote-user docker \
--ssh-path-to-private-key `minikube ssh-key` \
--ssh-password `minikube ssh-password` \
--override-ssh-host `minikube ip` \
```


## Kubectl

In order to use `kubectl` action, you're going to need `kubectl` accessible in your path. The official images ship with the latest minor version of `kubectl` inside of the container.
