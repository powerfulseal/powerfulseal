---
layout: default
title: Contribute
nav_order: 8
description: ""
permalink: /contribute
---

# Contribute to PowerfulSeal
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Testing

PowerfulSeal uses [tox](https://github.com/tox-dev/tox) to test multiple Python versions in a straightforward manner.

### Installation

In order to use `tox`, `tox` must be installed and Python binaries for the versions listed in [tox.ini](https://github.com/bloomberg/powerfulseal/blob/master/tox.ini) must be visible in your PATH.

Due to the difficulty in maintaining the required libraries for so many Python versions, it is recommended to use [pyenv](https://github.com/pyenv/pyenv) to install and manage multiple versions of Python.

The recommended installation steps are:
1. Install pyenv using the [Basic GitHub Checkout](https://github.com/pyenv/pyenv#basic-github-checkout) method
2. Run `pyenv install --list`
3. For every version specified in `tox.ini`, find the latest patch version corresponding to the version (e.g., `3.7` -> `3.7.5`) and run `pyenv install [version]`
4. In this project's root directory, run `pyenv local [versions]`, where `[versions]` is a space-separated list of every version you just installed (e.g., `pyenv local 3.7.0`)
5. Run `pyenv which 3.7`, etc. and ensure there are no errors and the output path is a `.pyenv` directory

### Usage

With the installation complete, simply run `tox` (or the analagous `make test`). If you are running on a machine with `inotifywait` installed (i.e., a UNIX machine), you can run `make watch` and run tests automatically when you run changes.

You can also run tests for specific versions by running `tox -e [version(s)]` (e.g., `tox -e py36`). Additionally, if you need to reinstall dependencies, you can use the `-r` flag.

## Docs

We use Jekyll for the documentation. In order to host/generate the docs locally, you have to follow [this](https://help.github.com/en/github/working-with-github-pages/testing-your-github-pages-site-locally-with-jekyll) tutorial.