---
layout: default
title: Writing policies
nav_order: 4
description: ""
permalink: /policies
has_children: true
---

# Policies
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---


## Syntax

Policies describe the chaos experiments for powerfulseal to execute in autonomous mode. The syntax is formally defined [here](https://github.com/powerfulseal/powerfulseal/blob/master/powerfulseal/policy/ps-schema.yaml). If you want to browse the available options, see below:

[Browse the syntax documentation](./schema){: .btn .btn-secondary .fs-5 .mb-4 .mb-md-0 .mr-2 }


## Basic structure

### Empty scenario

A policy file is a yaml file. The most basic policy you can write is the following:

```yaml
scenarios: []
```

It will validate, but will not do anything interesting.

### Kitchen sink

If you'd like to see all possible options in an example config, you [this policy](https://github.com/powerfulseal/powerfulseal/blob/master/tests/policy/example_config.yml). We use it to test that it validates to detect any regressions when new features are added.


## Scenarios

Every scenario has a name and an array of steps to do. For example:

```yaml
scenarios:
- name: Example scenario
  description: >
    A longer description of the scenario.
    Can have multiple lines etc.
  steps: []
```

The steps will be executed in the order specified.


## Config

You can also tweak certain parameters directly from the policy file.

### Number of runs

For example, by default the seal will continuosly run your scenario and only stop on errors.

If you'd like to run an experiment as part of your CI pipeline, you might want to run it a single time and then exit. The return code will tell you whether the experiment succeeded or not.

```yaml
config:
  runStrategy:
    runs: 1
scenarios: []
```

### Order of scenarios

By default, the seal runs the scenarios in the order specified (`round-robin`). You can change that to run them in a random order:


```yaml
config:
  runStrategy:
    strategy: random
scenarios: []
```

### Exit strategy

By default, if a scenario fails, the seal will report the error so that you can alert on it, and keep going.

If you'd like it to exit (for example if you're running it as a job), you can use the `fail-fast` exit strategy:

```yaml
config:
  exitStrategy:
    strategy: fail-fast
scenarios: []
```

## Examples

To see examples of policies, use the menu on the left.


## Note on self-destruction

With great power comes great responsibility, and sometimes it's easy to take down the wrong pod or node and kill the Seal by accident.

That's not ideal, because it might result in nodes staying down, or incomplete experiments.

To avoid that, PowerfulSeal honors two variables, that it will filter out from killing:

```yaml
          env:
          # in order to allow PowerfulSeal to not accidentally self-destruct
          # give it the pod name
          - name: POD_NAME
            valueFrom:
              fieldRef:
                apiVersion: v1
                fieldPath: metadata.name
          # and the host ip
          - name: HOST_IP
            valueFrom:
              fieldRef:
                apiVersion: v1
                fieldPath: status.hostIP
```

Any pods with this name, and any hosts with that IP will be spared.
