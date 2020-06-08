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

Autonomous mode is the workhorse of the seal. Once you know what kind of experiment you're after, you can write a yaml file to describe that. For more information on running the autonomous mode, see the help:


```sh
$ seal autonomous --help
```

## Writing policies

To learn how to write policies, visit the [policies section](./policies)

## Metrics collection

Autonomous mode also comes with the ability for metrics useful for monitoring to be collected. PowerfulSeal currently has a `stdout`, Prometheus and Datadog collector. However, metric collectors are easily extensible so it is easy to add your own. More details can be found [here](./in-depth-topics#metric-collection).

For example, getting prometheus metrics is as simple as adding the flag `--prometheus-collector` when starting the seal.


## Web User Interface

⚠️ If you're not going to use the UI, use the flag `--headless` to disable it

PowerfulSeal comes with a web interface to help you navigate Autonomous Mode. Features include:

- viewing logs
- viewing the policy


[![web interface](./media/web.png)](https://github.com/bloomberg/powerfulseal/blob/master/docs/media/web.png)

