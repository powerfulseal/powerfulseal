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

- [Autonomous](./autonomous-mode) mode reads a policy file, which can contain any number of pod and node scenarios. Each scenario describes a list of matches, filters and actions to execute on your cluster, and will be executed in a loop.

- [Interactive](./interactive-mode) mode is designed to allow you to discover your cluster's components and manually break things to see what happens. It operates on nodes, pods, deployments and namespaces.

- [Label](./label-mode) mode allows you to specify which pods to kill with a small number of options by adding `seal/` labels to pods. This is a more imperative alternative to autonomous mode.