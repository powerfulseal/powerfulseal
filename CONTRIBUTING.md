# Contributing to `PowerfulSeal`

If you'd like to help us improve and extend this project, then we welcome your contributions!

Below you will find some basic steps required to be able to contribute to the project. If you have any questions about this process or any other aspect of contributing to a Bloomberg open source project, feel free to send an email to opensource@bloomberg.net and we'll get your questions answered as quickly as we can.

Pull Requests are always welcome, however they will only be accepted if they provide a reasonably test coverage.

## Contribution Licensing

Since `PowerfulSeal` is distributed under the terms of the [Apache Version 2 license](LICENSE), contributions that you make are licensed under the same terms. In order for us to be able to accept your contributions, we will need explicit confirmation from you that you are able and willing to provide them under these terms, and the mechanism we use to do this is called a Developer's Certificate of Origin [DCO](DCO.md).  This is very similar to the process used by the Linux(R) kernel, Samba, and many other major open source projects.

To participate under these terms, all that you must do is include a line like the following as the last line of the commit message for each commit in your contribution:

    Signed-Off-By: Random J. Developer <random@developer.example.org>

    The simplest way to accomplish this is to add `-s` or `--signoff` to your `git commit` command.

    You must use your real name (sorry, no pseudonyms, and no anonymous contributions).


## Testing

PowerfulSeal uses [tox](https://github.com/tox-dev/tox) to test multiple Python versions in a straightforward manner.

### Installation
In order to use `tox`, `tox` must be installed and Python binaries for the versions listed in [tox.ini](https://github.com/bloomberg/powerfulseal/blob/master/tox.ini) must be visible in your PATH.

Due to the difficulty in maintaining the required libraries for so many Python versions, it is recommended to use [pyenv](https://github.com/pyenv/pyenv) to install and manage multiple versions of Python.

The recommended installation steps are:
1. Install pyenv using the [Basic GitHub Checkout](https://github.com/pyenv/pyenv#basic-github-checkout) method
2. Run `pyenv install --list`
3. For every version specified in `tox.ini`, find the latest patch version corresponding to the version (e.g., `3.7` -> `3.7.0`) and run `pyenv install [version]`
4. In this project's root directory, run `pyenv local [versions]`, where `[versions]` is a space-separated list of every version you just installed (e.g., `pyenv local 3.7.0`)
5. Run `pyenv which 3.7`, etc. and ensure there are no errors and the output path is a `.pyenv` directory

### Usage

With the installation complete, simply run `tox` (or the analagous `make test`). If you are running on a machine with `inotifywait` installed (i.e., a UNIX machine), you can run `make watch` and run tests automatically when you run changes.

You can also run tests for specific versions by running `tox -e [version(s)]` (e.g., `tox -e py36`). Additionally, if you need to reinstall dependencies, you can use the `-r` flag.

## Docs

We use plain Markdown and Github Pages for the documentation. If you want to have a local environment [this](https://help.github.com/en/github/working-with-github-pages/testing-your-github-pages-site-locally-with-jekyll) is a good explanation.
