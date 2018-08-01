# Testing `PowerfulSeal`

PowerfulSeal uses [tox](https://github.com/tox-dev/tox) to test multiple Python versions in a straightforward manner, which is especially useful due to the application's compatibility with both Python 2.7 and Python 3.

## Installation
In order to use `tox`, `tox` must be installed and Python binaries for the versions listed in [tox.ini](tox.ini) (2.7, 3.4, 3.6, 3.7 as of writing) must be visible in your PATH.

Due to the difficulty in maintaining the required libraries for so many Python versions, it is recommended to use [pyenv](https://github.com/pyenv/pyenv) to install and manage multiple versions of Python.

The recommended installation steps are:
1. Install pyenv using the [Basic GitHub Checkout](https://github.com/pyenv/pyenv#basic-github-checkout) method
2. Run `pyenv install --list` 
2. For every version specified in `tox.ini`, find the latest patch version corresponding to the version (e.g., `2.7` -> `2.7.15`) and run `pyenv install [version]`
4. In this project's root directory, run `pyenv local [versions]`, where `[versions]` is a space-separated list of every version you just installed (e.g., `pyenv install 2.7.15 3.4.8 3.6.5 3.7.0`)
5. Run `pyenv which 2.7`, `pyenv which 3.4`, etc. and ensure there are no errors and the output path is a `.pyenv` directory 

## Usage

With the installation complete, simply run `tox` (or the analagous `make test`). If you are running on a machine with `inotifywait` installed (i.e., a UNIX machine), you can run `make watch` and run tests automatically when you run changes.

You can also run tests for specific versions by running `tox -e [version(s)]` (e.g., `tox -e py36`). Additionally, if you need to reinstall dependencies, you can use the `-r` flag.