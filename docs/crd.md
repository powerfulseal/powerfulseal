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

## Kubernetes Installation

- Apply the rbac.yml (choose the appropriate namespace) to setup a service account with sufficient privileges

  `kubectl apply -f kubernetes/bac.yml`

- Apply Powerseal deployment
  `kubectl apply -f kubernetes/powerfulseal.yml`

- Deploy base powerseal configuration
  `kubectl apply -f kubernetes/policy.yml`

## CRD Installation

- Create the Custom Resource Definition
    `kubectl apply -f kubernetes/rbac.yml`

## Create a Scenario

An example scenario is provided
    `kubectl apply -f kubernetes/scenario_example.yml`
