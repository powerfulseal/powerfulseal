# PowerfulSeal

__PowerfulSeal__ adds chaos to your Kubernetes clusters, so that you can detect problems in your systems as early as possible. It kills targeted pods and takes VMs up and down.

It follows the [Principles of Chaos Engineering](http://principlesofchaos.org/), and is inspired by [Chaos Monkey](https://github.com/Netflix/chaosmonkey).

Embrace the inevitable failure. __Embrace The Seal__.

[![PyPI](https://img.shields.io/pypi/v/powerfulseal.svg)](https://pypi.python.org/pypi/powerfulseal)
[![Travis](https://img.shields.io/travis/bloomberg/powerfulseal.svg)](https://travis-ci.org/bloomberg/powerfulseal)

[Watch us introduce the Seal at Kubecon 2017 Austin](https://youtu.be/00BMn0UjsG4)


## Introduction

__PowerfulSeal__ works in two modes: interactive and autonomous.

__Interactive__ mode is designed to allow you to discover your cluster's components, and manually break things to see what happens. It operates on nodes, pods, deployments and namespaces.

__Autonomous__ mode reads a policy file, which can contain any number of pod and node scenarios. Each scenario describes a list of matches, filters and actions to execute on your cluster.

## Interactive mode

Here's a sneak peek of what you can do in the interactive mode:

![demo nodes](./media/video-nodes.gif)

![demo pods](./media/video-pods.gif)


## Autonomous mode

Autonomous reads the scenarios to execute from the policy file, and runs them:

1. The matches are combined together and deduplicated to produce an initial working set
2. They are run through a series of filters
3. For all the items remaining after the filters, all actions are executed

![pipeline](./media/pipeline.png)


## Writing policies

A minimal policy file, doing nothing, looks like this:

```yaml
config:
  minSecondsBetweenRuns: 77
  maxSecondsBetweenRuns: 100

nodeScenarios: []

podScenarios: [] 
```

The schemas are validated against the [powerful JSON schema](./powerfulseal/policy/ps-schema.json)

A [full featured example](./tests/policy/example_config.yml) listing most of the available options can be found in the [tests](./tests/policy).

## Setup


Setup includes:
- pointing PowerfulSeal at your Kubernetes cluster by giving it a Kubernetes config file
- pointing PowerfulSeal at your cloud by specifying the cloud driver to use and providing credentials
- making sure that PowerfulSeal can SSH into the nodes to execute commands on them
- writing a set of policies

These interactions are available:

![pipeline](./media/setup.png)

## Getting started

`PowerfulSeal` is available to install through pip:

```sh
pip install powerfulseal
powerfulseal --help # or seal --help
```

## Read about the PowerfulSeal

- https://www.techatbloomberg.com/blog/powerfulseal-testing-tool-kubernetes-clusters/
- https://siliconangle.com/blog/2017/12/17/bloomberg-open-sources-powerfulseal-new-tool-testing-kubernetes-clusters/
- https://github.com/ramitsurana/awesome-kubernetes#testing
- https://github.com/ramitsurana/awesome-kubernetes#other-useful-videos
- https://github.com/dastergon/awesome-chaos-engineering#notable-tools
- https://www.linux.com/news/powerfulseal-testing-tool-kubernetes-clusters-0


## FAQ

### Where can I learn more about Chaos Engineering ?

We found these two links to be a good start:

- http://principlesofchaos.org/
- https://github.com/dastergon/awesome-chaos-engineering

### How is it different from Chaos Monkey ?

PowerfulSeal was inspired by Chaos Monkey, but it differs in a couple of important ways.

The Seal does:
  - speak Kubernetes
  - offer flexible, easy to write YAML scenarios
  - provide interactive mode with awesome tab-completion

The Seal doesn't:
  - need external dependencies (db, Spinnaker), apart from SSH, cloud and Kubernetes API access
  - need you to setup ```cron```

### Can I contribute to The Seal ?

We would love you to. In particular, it would be great to get help with:

- get more [cloud drivers](./powerfulseal/clouddrivers/driver.py)
- get more [awesome filters](./powerfulseal/policy/scenario.py)
- __get an amazing logo__
- make the PowerfulSeal more powerful

Check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for more information about how to contribute.

### Why a Seal ?

It might have been inspired by [this comic](https://randowis.com/2015/01/07/the-tower/)

