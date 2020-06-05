---
layout: default
title: Modes
nav_order: 3
description: ""
permalink: /modes
has_children: true
---

# Modes

__PowerfulSeal__ works in several modes:

- [Autonomous](./autonomous-mode) mode reads a policy file, that can contain any number of scenarios. It will continuously execute the desired scenarios and produce metrics. This is designed for when you know what kind of failure you'd like to inject into your cluster.

- [Interactive](./interactive-mode) mode is designed to allow you to discover your cluster's components and manually break things to see what happens. It has fewer features than the autonomous mode and should be used during the initial phase of planning a chaos experiment.

- [Label](./label-mode) mode allows you to specify which pods to kill with a small number of options by adding `seal/` labels to pods. This is a more imperative alternative to autonomous mode.
