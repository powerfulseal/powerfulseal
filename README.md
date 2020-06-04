
# PowerfulSeal

[![Travis](https://img.shields.io/travis/bloomberg/powerfulseal.svg)](https://travis-ci.com/bloomberg/powerfulseal) [![PyPI](https://img.shields.io/pypi/v/powerfulseal.svg)](https://pypi.python.org/pypi/powerfulseal)

__PowerfulSeal__ adds chaos to your Kubernetes clusters, so that you can detect problems in your systems as early as possible. It kills targeted pods and takes VMs up and down.



<p align="center">
  <img src="docs/media/powerful-seal.png" alt="Powerful Seal Logo" width="200"></a>
  <br>
  Embrace the inevitable failure. <strong>Embrace The Seal</strong>.
  <br>
  <br>
</p>

It follows the [Principles of Chaos Engineering](http://principlesofchaos.org/), and is inspired by [Chaos Monkey](https://github.com/Netflix/chaosmonkey). [Watch the Seal at KubeCon 2017 Austin](https://youtu.be/00BMn0UjsG4).

## Highlights

- works with `OpenStack`, `AWS`, `Azure`, `GCP` and local machines
- speaks `Kubernetes` natively
- interactive and autonomous, policy-driven mode
- web interface to interact with PowerfulSeal
- metric collection and exposition to `Prometheus` or `Datadog`
- minimal setup, easy yaml-based policies
- easy to extend

## Documentation

[Powerfulseal documentation](https://bloomberg.github.io/powerfulseal) is included in the docs directory. It can be hosted locally with jekyll by running jekyll serve from the docs directory.

## Read about the PowerfulSeal

- https://medium.com/faun/failures-are-inevitable-even-a-strongest-platform-with-concrete-operations-infrastructure-can-7d0c016430c6
- https://www.techatbloomberg.com/blog/powerfulseal-testing-tool-kubernetes-clusters/
- https://siliconangle.com/blog/2017/12/17/bloomberg-open-sources-powerfulseal-new-tool-testing-kubernetes-clusters/
- https://github.com/ramitsurana/awesome-kubernetes#testing
- https://github.com/ramitsurana/awesome-kubernetes#other-useful-videos
- https://github.com/dastergon/awesome-chaos-engineering#notable-tools
- https://www.linux.com/news/powerfulseal-testing-tool-kubernetes-clusters-0
- https://www.infoq.com/news/2018/01/powerfulseal-chaos-kubernetes

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

- get more [cloud drivers](https://bloomberg.github.io/powerfulseal/in-depth-topics#custom-cloud-drivers)
- get more [awesome filters](https://bloomberg.github.io/powerfulseal/in-depth-topics#custom-filters)
- <del>__get an amazing logo__</del>
- make the PowerfulSeal more powerful

Check out our [contributing](https://bloomberg.github.io/powerfulseal/contribute) page for more information about how to contribute.

### Why a Seal ?

It might have been inspired by [this comic](https://randowis.com/2015/01/07/the-tower/).


## Footnotes

PowerfulSeal logo Copyright 2018 The Linux Foundation, and distributed under the Creative Commons Attribution (CC-BY-4.0) [license](https://creativecommons.org/licenses/by/4.0/legalcode).