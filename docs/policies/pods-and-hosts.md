---
layout: default
title: Stop a host running particular pod
description: ""
permalink: /stop-host-running-a-pod 
parent: Writing policies
nav_order: 8
---

# Stop a host running particular pod
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

You might want to stop a host that runs a particular set of pods. You can do that with `stopHost` action for pods.


## Scenario

```yaml
scenarios:
- name: Stop that host!
  steps:
  - podAction:
      matches:
        - namespace: something
      filters:
        - randomSample:
            size: 1
      actions:
        - stopHost:
            autoRestart: true
  - wait:
      seconds: 30

```

This will stop the host running that pod, and restart at the end of the scenario.
