---
layout: default
title: Taking VMs down
description: ""
permalink: /master-node
parent: Writing policies
nav_order: 3
---

# Taking VMs down
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

Let's say that you'd like to make sure that if one of the VMs in your cluster goes down (let's say one that's running master nodes), some service running on them still works well.

Well, PowerfulSeal can do that for you.

### Cloud drivers

If you'd like to modify the state of VMs, you're going to need to configure a cloud driver. You can learn how to do that [here](cloud-provider-requirements).

## Policy


```yaml
- name: Test load-balancing on master nodes
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

  # issue an HTTP probe to the url of the service we expect to see up
  - probeHTTP:
      target:
        url: "http://load-balancer.example.com"
      # we can allow some retries, if needed
      retries: 3
      # we can also make more requests to make sure we hit all instances
      count: 100

  # restart the node which are down
  - nodeAction:
      # pick all master VMs
      matches:
        - propertyNode:
            name: "name"
            value: ".*master.*"
      filters:
        # filter down to only the VMs which are in DOWN state
        - propertyNode:
            name: "state"
            value: "DOWN"
      actions:
        - start
```
