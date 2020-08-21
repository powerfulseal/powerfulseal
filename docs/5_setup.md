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

- creating [RBAC rules](https://github.com/powerfulseal/powerfulseal/blob/master/kubernetes/rbac.yml) to allow the seal to list, get and delete pods and nodes,
  - you might need to adjust it depending on what you are planning to do with the Seal
- creating a [configmap and deployment](https://github.com/powerfulseal/powerfulseal/blob/master/kubernetes/powerfulseal.yml)
  - your scenarios will live in the configmap
  - if you'd like to use the UI, you'll probably also need a service and ingress

That's it. The Seal will self-discover the way to connect to `Kubernetes` and start executing your policy


## Running outside of the cluster

If you're running outside of your cluster, the setup will involve:

- pointing PowerfulSeal at your Kubernetes cluster by giving it a Kubernetes config file
- pointing PowerfulSeal at your cloud by specifying the cloud driver to use and providing credentials
- making sure the Seal can `SSH` into the nodes in order to execute `docker kill` command
- writing a set of policies

It should look something like [this](https://github.com/powerfulseal/powerfulseal/blob/master/docs/media/setup.png).


## Kubectl

The `powerfulseal` image packages a `kubectl` binary to execute the `kubectl` actions with.
When executing the commands, the `http{s}_proxy` variables are overwritten by the contents of the `proxy` parameter from inside of the scenario.

If you exec into the pod, you can `kubectl` directly, using the same RBAC permissions.

For example, in the [./kubernetes](https://github.com/powerfulseal/powerfulseal/tree/master/kubernetes) contains RBAC which allows the seal to:

- read from all namespaces
- delete pods in all namespaces
- do everything inside of the special `powerfulseal-sandbox` namespace
  - all creation of new pods will need to happen inside of that namespace


### `kubectl` action permissions

Remember, that in order to be able to execute the `kubectl` action payloads, you're going to need to give you pod necessary permissions.



## Exec-ing into a running pod

If you have a running `powerfulseal` pod executing scenario, you can always `kubectl exec -ti ps-pod -- bash` and then run `powerfulseal interactive` from inside of it.


## Cloud drivers

In order to interact with VMs, you're going to need to configure a cloud driver. [Learn more](./cloud-provider-requirements)


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
