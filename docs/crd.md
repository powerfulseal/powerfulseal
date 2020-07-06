---
layout: default
title: Kubernetes Custom Resources
nav_order: 2
description: ""
permalink: /crd
parent: Setup
---

## Kubernetes Custom Resource Definition
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

`Powerfulseal` can be deployed on Kubernetes cluster to perform random chaos the application services.
It also allows teams to define scenarios in their own namespace using [Kubernetes Custom Resources (CRD)](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/).
Powerfulseal adds all CRD-defined scenarios to the ones defined in the policy configuration file (optional).
*Scenarios are reloaded after the execution of the current run.*

## Kubernetes Installation

- Apply the rbac.yml (choose the appropriate namespace) to setup a service account with sufficient privileges

  `kubectl apply -f kubernetes/rbac.yml`

- Deploy powerful seal
  `kubectl apply -f kubernetes/powerfulseal.yml`

## CRD Installation

- Create the Custom Resource Definition
    `kubectl apply -f kubernetes/crd.yml`

## Deploy Example

An example scenario is provided. This creates a sandbox namespace with 2 nginx replicas and ensures their resilience
    `kubectl apply -f kubernetes/sandbox.yml`
    `kubectl apply -f kubernetes/sandbox_scenario.yml`
