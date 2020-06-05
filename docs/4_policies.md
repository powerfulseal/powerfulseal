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

A policy file is a yaml file. The most basic policy you can write is the following:

```yaml
scenarios: []
```

It will validate, but will not do anything interesting.

### Kitchen sink

If you'd like to see all possible options in an example config, you [this policy](https://github.com/bloomberg/powerfulseal/blob/master/tests/policy/example_config.yml). We use it to test that it validates to detect any regressions when new features are added.
