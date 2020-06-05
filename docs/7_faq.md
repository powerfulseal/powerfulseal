---
layout: default
title: FAQ
nav_order: 7
description: ""
permalink: /faq
---

# Frequently Asked Questions
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## FAQ

### Where can I learn more about Chaos Engineering ?

We found these two links to be a good start:

- [http://principlesofchaos.org/](http://principlesofchaos.org/)
- [https://github.com/dastergon/awesome-chaos-engineering](https://github.com/dastergon/awesome-chaos-engineering)


### How is it different from Chaos Monkey ?

PowerfulSeal was inspired by Chaos Monkey, but it differs in a couple of important ways.

The Seal does:
  - speak Kubernetes
  - offer flexible, easy to write YAML scenarios
  - provide interactive mode with awesome tab-completion

The Seal doesn't:
  - need external dependencies (db, Spinnaker), apart from SSH, cloud and Kubernetes API access
  - need you to setup ```cron```
  - rely on randomness for all of your experiments

### Can I contribute to The Seal ?

We would love you to. In particular, it would be great to get help with:

- get more [cloud drivers](https://bloomberg.github.io/powerfulseal/in-depth-topics#custom-cloud-drivers)
- get more [awesome filters](https://bloomberg.github.io/powerfulseal/in-depth-topics#custom-filters)
- <del>__get an amazing logo__</del>
- make the PowerfulSeal more powerful

Check out our [contributing](https://bloomberg.github.io/powerfulseal/contribute) page for more information about how to contribute.

### Why a Seal ?

It might have been inspired by [this comic](https://randowis.com/2015/01/07/the-tower/).