---
layout: default
title: Pods reschedule SLO
description: ""
permalink: /pods-rescheduled
parent: Writing policies
nav_order: 2
---

# Pods reschedule SLO
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

Let's say we want to verify that if pod is deleted, it will be rescheduled and running with a specified time.

You can do that easily with the Seal.

## Policy


```yaml
scenarios:
- name: Check pod rescheduling SLO
  description: >
    Verifies that after a pod is killed,
    it's succesfully rescheduled after 30 seconds.
  steps:

  # kill a pod
  - podAction:
      matches:
        - namespace: kube-system
      filters:
        - randomSample:
            size: 1
      actions:
        - kill:

  # wait the minimal time for the SLO
  - wait:
      seconds: 30

  # make sure all pods are running in the namespace
  - podAction:
      matches:
        - namespace: kube-system
      actions:
        - checkPodState:
            state: Running
        - checkPodCount:
            count: 2
```
