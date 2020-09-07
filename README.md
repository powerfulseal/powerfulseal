
# PowerfulSeal

[![Travis](https://img.shields.io/travis/powerfulseal/powerfulseal.svg)](https://travis-ci.com/powerfulseal/powerfulseal) [![PyPI](https://img.shields.io/pypi/v/powerfulseal.svg)](https://pypi.python.org/pypi/powerfulseal)

**PowerfulSeal** injects failure into your Kubernetes clusters, so that you can detect problems as early as possible. It allows for writing scenarios describing complete [chaos experiments](https://principlesofchaos.org).

<p align="center">
  <img src="docs/media/powerful-seal.png" alt="Powerful Seal Logo" width="150"></a>
  <br>
  Embrace the inevitable failure. <strong>Embrace The Seal</strong>.
  <br>
</p>

## [Documentation](https://powerfulseal.github.io/powerfulseal)

Please refer to the [Powerfulseal documentation](https://powerfulseal.github.io/powerfulseal) to learn how to use it.

## Highlights

- works with `Kubernetes`, `OpenStack`, `AWS`, `Azure`, `GCP` and local machines
- `yaml` [policies](https://powerfulseal.github.io/powerfulseal/policies) describing complete chaos experiments
- `Prometheus` and `Datadog` metrics collection
- multiple [modes](https://powerfulseal.github.io/powerfulseal/modes) for differnt use cases


## Hello world!

Just to give you a taste, here's an example policy. It will kill a single pod, and then check that the service continues responding to HTTP probes, to verify its resiliency to one of its pods going down.

```yaml
scenarios:
- name: Kill one pod in my namespace, make sure the service responds
  steps:
  # kill a pod from `myapp` namespace
  - podAction:
      matches:
        - namespace: myapp
      filters:
        - randomSample:
            size: 1
      actions:
        - kill:
            probability: 0.75
  # check my service continues working
  - probeHTTP:
      target:
        service:
          name: my-service
          namespace: myapp
      endpoint: /healthz
```

Assuming that's in `policy.yml`, you can run it like this:

```sh
powerfulseal autonomous --policy-file ./policy.yaml
```

[Learn more](https://powerfulseal.github.io/powerfulseal)

## Installing

- [docker hub](https://hub.docker.com/r/powerfulseal/powerfulseal/tags): `docker pull powerfulseal/powerfulseal:3.1.1`
- [pip](https://pypi.org/project/powerfulseal/): `pip install powerfulseal`


## Read about the PowerfulSeal

- https://medium.com/faun/failures-are-inevitable-even-a-strongest-platform-with-concrete-operations-infrastructure-can-7d0c016430c6
- https://www.techatbloomberg.com/blog/powerfulseal-testing-tool-kubernetes-clusters/
- https://siliconangle.com/blog/2017/12/17/bloomberg-open-sources-powerfulseal-new-tool-testing-kubernetes-clusters/
- https://github.com/ramitsurana/awesome-kubernetes#testing
- https://github.com/ramitsurana/awesome-kubernetes#other-useful-videos
- https://github.com/dastergon/awesome-chaos-engineering#notable-tools
- https://www.linux.com/news/powerfulseal-testing-tool-kubernetes-clusters-0
- https://www.infoq.com/news/2018/01/powerfulseal-chaos-kubernetes
- [PowerfulSeal presentation at KubeCon 2017 Austin](https://youtu.be/00BMn0UjsG4)


## Tools consuming PowerfulSeal

- Chaos and resiliency testing tool for Kubernetes and OpenShift: https://github.com/openshift-scale/kraken

---

## Footnotes

PowerfulSeal logo Copyright 2018 The Linux Foundation, and distributed under the Creative Commons Attribution (CC-BY-4.0) [license](https://creativecommons.org/licenses/by/4.0/legalcode).
