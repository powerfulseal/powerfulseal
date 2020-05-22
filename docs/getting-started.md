---
layout: default
title: Getting Started
nav_order: 2
description: ""
permalink: /getting-started
---

# Getting started
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

`PowerfulSeal` is available to install through pip:

```sh
pip install powerfulseal
powerfulseal --help # or seal --help
```

To start the web interface, use flags `--server --server-host [HOST] --server-port [PORT]` when starting PowerfulSeal in autonomous mode and visit the web server at `http://HOST:PORT/`.

Python 3.6, Python 3.7 and Python 3.8 are supported.


## Docker

The automatically built docker images are now available on [docker hub](https://hub.docker.com/_/powerfulseal)

```sh
docker pull bloomberg/powerfulseal:2.7.0
```