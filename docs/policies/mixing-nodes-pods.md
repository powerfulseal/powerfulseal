---
layout: default
title: Mixing nodes and pods
description: ""
permalink: /mixing-nodes-and-pods 
parent: Writing policies
nav_order: 6
---

# Mixing nodes and pods
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

A single scenario can have actions on both nodes and pods (don't forget to configure a cloud driver).

For example, imagine that you have a service which resolves to a daemonset, and you want to check that the service won't return an error if a node is taken down.


## Scenario

```yaml
scenarios:
- name: Check service responds when one node lost
  steps:

  # take down a single master VM
  - nodeAction:
      # pick all master VMs
      matches:
        - propertyNode:
            name: "name"
            value: ".*master.*"
      filters:
        # only pick the VMs which are in UP state
        - propertyNode:
            name: "state"
            value: "UP"
        # and only pick a single VM
        - randomSample:
            size: 1
      actions:
        - stop:
            force: false

  # make sure the service responds
  - probeHTTP:
      target:
        service:
          name: myservice
          namespace: example
          port: 8000
      # assuming we had a 100 nodes, and it goes in round-robin
      # we can make 100 calls to the service
      count: 100
```
