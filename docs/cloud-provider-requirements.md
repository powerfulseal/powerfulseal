---
layout: default
title: Cloud Provider
nav_order: 2
description: ""
permalink: /cloud-provider-requirements
parent: Setup
---

## Cloud Provider Requirements
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---
## SSH

In all cases, the SSH Keys must be set up for SSH Client access of the nodes.  

> Note: With GCP, running ```gcloud compute config-ssh``` makes SSHing to node instances easier by adding an alias for each instance to the user SSH configuration (~/.ssh/config) file and then being able to use the generated file with ```--ssh-path-to-private-key``` argument.


## Azure

The credentials to connect to Azure may be specified in one of two ways:

1. Supply the full path to an Azure credentials file in the environment variable `AZURE_AUTH_LOCATION`.  
This is the easiest method.  The credentials file can be generated via `az aks get-credentials -n <cluster name> -g <resource group> -a -f <destination credentials file>`
2. Supply the individual credentials in the environment variables: `AZURE_SUBSCRIPTION_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

## AWS

The credentials to connect to AWS are specified the same as for the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)

## OpenStack

The easiest way to use PowerfulSeal, is to download and source the OpenRC file you can get from Horizon. It should ask you for your password, and it should set all the `OS_*` variables for you. Alternatively, you can set them yourself.

Both approaches are detailed in [the official documentation](https://docs.openstack.org/mitaka/user-guide/common/cli_set_environment_variables_using_openstack_rc.html).


## GCP

>Google Cloud SDK and kubectl are required

The GCP cloud driver supports managed (GKE) and custom Kubernetes clusters running on top of Google Cloud Compute.

For setting up ```PowerfulSeal```, the first step is configuring gcloud SDK (as ```PowerfulSeal``` will work with your configured [project](https://cloud.google.com/resource-manager/docs/creating-managing-projects) and [region](https://cloud.google.com/compute/docs/regions-zones/changing-default-zone-region)) and pointing kubectl to your cluster. Both can be configured easily following [this](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl) tutorial (For GKE!). In case you don't want to use the default project/region of gcloud SDK, you can point ```PowerfulSeal``` to the correct one (in json) with ```--gcp-config-file``` argument.

For being able to run node related commands, credentials have to be specified in one of these [ways](https://cloud.google.com/docs/authentication/):

1. Service account (Recommended): a Google account that is associated with your GCP project, as opposed to a specific user. ```PowerfulSeal``` uses the environment variable and is pretty straightforward to set up using [this](https://cloud.google.com/docs/authentication/getting-started) tutorial.
2. User account: Not recommended as you can reach easily reach a "quota exceeded" or "API not enabled" error. ```PowerfulSeal``` uses auto-discovery and to get it working just follow [this](https://cloud.google.com/docs/authentication/end-user).

Having configuration ready and ssh connection to the node instances working, you can start playing with ```PowerfulSeal``` with this example:
```powerfulseal interactive --kubeconfig ~/.kube/config --gcp --inventory-kubernetes --ssh-allow-missing-host-keys --ssh-path-to-private-key ~/.ssh/google_compute_engine --remote-user myuser```

> Note: In case of running inside Pyenv and getting ```python2 command not found``` error when running gcloud (and you want to run ```PowerfulSeal``` with Python 3+), [this](https://github.com/pyenv/pyenv/issues/1159#issuecomment-453906182) might be useful, as gcloud requires Python2.
