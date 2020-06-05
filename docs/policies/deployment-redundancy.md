---
layout: default
title: Deployment redundancy
description: ""
permalink: /deployment-redundancy
parent: Writing policies
nav_order: 4
---

# Deployment redundancy
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

Let's say you have a deployment (`mydeployment`), fronted by a service (`myservice`). The deployment has 3 instances, and in theory, you should be able to lose one with no traffic down.

Let's test that. But only during the week, and before lunch, just in case something does break.

## Policy


```yaml
scenarios:
- name: Deployment redundancy
  steps:
  - podAction:
      matches:
        - deployment:
            name: mydeployment
            namespace: example
      filters:
        # to restrict the actions to work days, you can do
        - dayTime:
            onlyDays:
              - monday
              - tuesday
              - wednesday
              - thursday
              - friday
            startTime:
              hour: 10
              minute: 0
              second: 0
            endTime:
              hour: 12
              minute: 30
              second: 0

        - randomSample:
            size: 1
      actions:
        - kill:
            force: false

  # make sure the service responds
  - probeHTTP:
      target:
        service:
          name: myservice
          namespace: example
          port: 8000
```
