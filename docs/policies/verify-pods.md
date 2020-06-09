---
layout: default
title: Verify pod status
description: ""
permalink: /verify 
parent: Writing policies
nav_order: 5
---

# Verify pod status
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

You can also use `PowerfulSeal` to just assert things about your cluster. 


## Check all pods are in Running state

```yaml
scenarios:
- name: Verify there only running pods
  steps:
  - podAction:
      matches:
        - namespace: "*"
      filters:
        # pods not running
        - property:
            name: state
            value: Running
            negative: true
        - randomSample:
            size: 1
      actions:
        - checkPodCount:
            count: 0
```

## Count all pods with a label

```yaml
scenarios:
- name: Count pods with a specific label
  steps:
  - podAction:
      matches:
        - labels:
            namespace: "*"
            selector: important=true
      actions:
        - checkPodCount:
            count: 78
```
