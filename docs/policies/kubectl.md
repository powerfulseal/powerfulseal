---
layout: default
title: New pod startup SLO
description: ""
permalink: /kubectl
parent: Writing policies
nav_order: 1
---

# New pod startup SLO
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
- name: Test deployment SLO
  description: >
    Verifies that after a new deployment and a service are scheduled,
    it can be called within 30 seconds.
  steps:

  # you can use this to setup kubernetes artifacts
  - kubectl:
      # with auto delete, it will delete what's created here at the end of scenario
      autoDelete: true
      # equivalent to `kubectl apply -f -`
      action: apply
      payload: |
        ---
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: sealpolicy
        data:
          policy.yml: |-
            scenarios:
            - name: "noop"
              steps:
              - wait:
                  seconds: 1000
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
              containers:
                - name: powerfulseal
                  image: store/bloomberg/powerfulseal:3.0.0rc3
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
            port: 8000
        selector:
            name: powerfulseal

  # wait the minimal time for the SLO
  - wait:
      seconds: 30

  # make sure the service responds
  - probeHTTP:
      target:
        service:
          name: some-service
          namespace: default
          port: 8000
          protocol: http
```
