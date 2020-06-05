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

Policies describe the chaos experiments for powerfulseal to execute in autonomous mode. The syntax is formally defined [here](https://github.com/bloomberg/powerfulseal/blob/master/powerfulseal/policy/ps-schema.yaml). If you want to browse the available options, see below:

[Browse the syntax documentation](./schema){: .btn .btn-secondary .fs-5 .mb-4 .mb-md-0 .mr-2 }


## Basic structure

### Empty scenario

A policy file is a yaml file. The most basic policy you can write is the following:

```yaml
scenarios: []
```

It will validate, but will not do anything interesting.

### Kitchen sink

If you'd like to see all possible options in an example config, you [this policy](https://github.com/bloomberg/powerfulseal/blob/master/tests/policy/example_config.yml). We use it to test that it validates to detect any regressions when new features are added.


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
```

### Order of scenarios

By default, the seal runs the scenarios in the order specified (`round-robin`). You can change that to run them in a random order:


```yaml
config:
  runStrategy:
    strategy: random
```

## Examples

To see examples of policies, use the menu on the left.
