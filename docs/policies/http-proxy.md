---
layout: default
title: Different proxies for probes
description: ""
permalink: /http-proxy-http_proxy 
parent: Writing policies
nav_order: 7
---

# Different proxies for probes
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Scenario

Sometimes you need different proxies for different HTTP probes.


## Scenario

```yaml
scenarios:
- name: Proxies
  steps:

  # no proxies needed in cluster
  - probeHTTP:
      target:
        service:
          name: myservice
          namespace: example
          port: 8000

  # for this url, we need a special proxy
  - probeHTTP:
      target:
        url: https://something.somewhere.com
      proxy: http://some-proxy:8080

  # note, that this will ignore HTTP_PROXY and HTTPS_PROXY in the env
  # at will go without proxies
  - probeHTTP:
      target:
        url: https://something.somewhere.com

```
