# Copyright 2018 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pytest
from mock import patch, MagicMock

import powerfulseal
from powerfulseal.cli.__main__ import parse_args

HOME = os.path.expanduser("~")


def test_flag_takes_precedence(monkeypatch, tmpdir):
    p1 = tmpdir.join("kubeconfig1")
    p1.write("{}")
    p2 = tmpdir.join("kubeconfig2")
    p2.write("{}")
    monkeypatch.setenv('KUBECONFIG', str(p1.realpath()))
    with patch("powerfulseal.cli.__main__.KUBECONFIG_DEFAULT_PATH", str(p2.realpath())):
        kube_config = powerfulseal.cli.__main__.parse_kubeconfig(parse_args([
            'interactive',
            '--kubeconfig', '~/LOL',
            '--inventory-kubernetes',
            '--no-cloud'
        ]))
        assert kube_config == HOME + "/LOL"


def test_env_var_takes_2nd_precedence(monkeypatch, tmpdir):
    p1 = tmpdir.join("kubeconfig1")
    p1.write("{}")
    p2 = tmpdir.join("kubeconfig2")
    p2.write("{}")
    monkeypatch.setenv('KUBECONFIG', str(p1.realpath()))
    with patch("powerfulseal.cli.__main__.KUBECONFIG_DEFAULT_PATH", str(p2.realpath())):
        kube_config = powerfulseal.cli.__main__.parse_kubeconfig(parse_args([
            'interactive',
            '--inventory-kubernetes',
            '--no-cloud'
        ]))
        assert kube_config == str(p1.realpath())


def test_home_kubeconfig_takes_3rd_precedence(monkeypatch, tmpdir):
    p2 = tmpdir.join("kubeconfig2")
    p2.write("{}")
    monkeypatch.delenv('KUBECONFIG', raising=False)
    with patch("powerfulseal.cli.__main__.KUBECONFIG_DEFAULT_PATH", str(p2.realpath())):
        kube_config = powerfulseal.cli.__main__.parse_kubeconfig(parse_args([
            'interactive',
            '--inventory-kubernetes',
            '--no-cloud'
        ]))
        assert kube_config == str(p2.realpath())


def test_in_cluster_takes_4th_precedence(monkeypatch, tmpdir):
    p2 = tmpdir.join("kubeconfig2")
    p2.write("{}")
    monkeypatch.delenv('KUBECONFIG', raising=False)
    with patch("powerfulseal.cli.__main__.KUBECONFIG_DEFAULT_PATH", "/probably/doesnt/exist"):
        kube_config = powerfulseal.cli.__main__.parse_kubeconfig(parse_args([
            'interactive',
            '--inventory-kubernetes',
            '--no-cloud'
        ]))
        assert kube_config == None