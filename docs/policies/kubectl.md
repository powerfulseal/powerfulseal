---
layout: default
title: New pod startup SLO
description: ""
permalink: /kubectl
parent: Writing policies
nav_order: 1
---

# Setup things to test
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

Let's say we want to make sure that a new pod you create responds quickly enough.

## Policy


```yaml
scenarios:
- name: Deploy a deployment, make sure it responds on its service within 30 seconds
  description: >
    Verifies that after a pod is killed,
    it's succesfully rescheduled after 30 seconds.
  steps:

  # you can use this to setup the
  - kubectl:
      action: apply
      # with auto delete, it will delete what's created here at the end of scenario
      autoDelete: true
      payload: |
        ---
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: sealpolicy
        data:
          policy.yml: |-
            scenarios:
            - name: "delete a random pod in default namespace"
              steps:
              - podAction:
                  matches:
                  - namespace: "default"
                  filters:
                  - randomSample:
                      size: 1
                  actions:
                  - kill:
                      probability: 0.77
                      force: true
        ---
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: powerfulseal
        spec:
          replicas: 1
          template:
            metadata:
              labels:
                name: powerfulseal
            spec:
              serviceAccountName: powerfulseal
              containers:
                - name: powerfulseal
                  image: store/bloomberg/powerfulseal:3.0.0
                  args:
                  - autonomous
                  - --policy-file=/policy.yml
                  volumeMounts:
                    - name: policyfile
                      mountPath: /policy.yml
                      subPath: policy.yml
              volumes:
                - name: policyfile
                  configMap:
                    name: sealpolicy
        ---
        apiVersion: v1
        kind: Service
        metadata:
        name: powerfulseal
        spec:
        ports:
        - name: powerfulseal
            port: 8080
        selector:
            name: powerfulseal

  # wait the minimal time for the SLO
  - wait:
      seconds: 30

  # make sure all pods are running in the namespace
  - probeHTTP:
      target:
        service:
          name: some-service
          namespace: default
          port: 9090
          protocol: http
```
