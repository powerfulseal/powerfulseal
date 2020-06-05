---
layout: default
title: Autonomous
nav_order: 3
description: ""
permalink: /autonomous-mode
parent: Modes
---

# Autonomous mode
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

Autonomous reads the scenarios to execute from the policy file, and runs them:

1. The matches are combined together and deduplicated to produce an initial working set
2. They are run through a series of filters
3. For all the items remaining after the filters, all actions are executed

```sh
$ seal autonomous --help
```

## Writing policies

A minimal policy file, doing nothing, looks like this:

```yaml
config:
  loopsNumber: 1 # will execute the provided scenarios once and then exit

nodeScenarios: []

podScenarios: [] 
```

A more interesting schema, that kills a random pod in `default` namespace every 1-30 seconds:

```yaml
config:
  # we don't set loopsNumber, so it will loop indefinitely
  minSecondsBetweenRuns: 1
  maxSecondsBetweenRuns: 30

nodeScenarios: []
podScenarios:
  - name: "delete random pods in default namespace"

    match:
      - namespace:
          name: "default"

    filters:
      - randomSample:
          size: 1

    actions:
      - kill:
          probability: 0.77
          force: true
```

A [full featured example](https://github.com/bloomberg/powerfulseal/blob/master/tests/policy/example_config.yml) listing most of the available options can be found in the [tests](https://github.com/bloomberg/powerfulseal/tree/master/tests/policy).

The schemas are validated against the [powerful YAML schema](https://github.com/bloomberg/powerfulseal/blob/master/powerfulseal/policy/ps-schema.yaml).


## Metrics collection

Autonomous mode also comes with the ability for metrics useful for monitoring to be collected. PowerfulSeal currently has a `stdout`, Prometheus and Datadog collector. However, metric collectors are easily extensible so it is easy to add your own. More details can be found [here](./in-depth-topics#metric-collection).


## Web User Interface

⚠️ If you're not going to use the UI, use the flag `--headless` to disable it

PowerfulSeal comes with a web interface to help you navigate Autonomous Mode. Features include:

- viewing logs
- viewing the policy


[![web interface](./media/web.png)](https://github.com/bloomberg/powerfulseal/blob/master/media/web.png)

