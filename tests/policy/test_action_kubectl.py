
# Copyright 2017 Bloomberg Finance L.P.
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


import random
import subprocess
import os

import pytest
from mock import MagicMock, patch


# noinspection PyUnresolvedReferences
from tests.fixtures import action_kubectl


def test_creates_cleanup_action(action_kubectl):
    action_kubectl.schema["action"] = "apply"
    action_kubectl.schema["autoDelete"] = True

    process = MagicMock()
    process.returncode = 0
    mock_run = MagicMock(return_value=process)
    with patch("subprocess.run", mock_run):
        assert action_kubectl.execute()

    assert mock_run.call_count == 1
    cleanup = action_kubectl.get_cleanup_actions()
    assert len(cleanup) == 1
    job = cleanup[0]
    assert job is not action_kubectl
    assert job.schema is not action_kubectl.schema
    assert job.schema["payload"] == action_kubectl.schema["payload"]
    assert job.schema["action"] == "delete"

def test_creates_cleanup_action_failure(action_kubectl):
    action_kubectl.schema["action"] = "apply"
    action_kubectl.schema["autoDelete"] = True

    process = MagicMock()
    process.returncode = 1
    mock_run = MagicMock(return_value=process)
    with patch("subprocess.run", mock_run):
        assert not action_kubectl.execute()

    assert mock_run.call_count == 1
    cleanup = action_kubectl.get_cleanup_actions()
    assert len(cleanup) == 1
    job = cleanup[0]
    assert job is not action_kubectl
    assert job.schema is not action_kubectl.schema
    assert job.schema["payload"] == action_kubectl.schema["payload"]
    assert job.schema["action"] == "delete"


def test_doesnt_create_cleanup_action(action_kubectl):
    action_kubectl.schema["autoDelete"] = False
    action_kubectl.execute()
    assert action_kubectl.get_cleanup_actions() == []


def test_passes_http_proxy(action_kubectl):
    proxy_value = "someproxy.com:8080"
    action_kubectl.schema["proxy"] = proxy_value
    action_kubectl.schema["action"] = "apply"
    action_kubectl.schema["payload"] = "payload"
    mock_run = MagicMock()

    with patch("subprocess.run", mock_run):
        action_kubectl.execute()

    assert mock_run.call_count == 1
    args = mock_run.call_args
    env = os.environ.copy()
    env["HTTP_PROXY"] = proxy_value
    env["HTTPS_PROXY"] = proxy_value
    env["http_proxy"] = proxy_value
    env["https_proxy"] = proxy_value
    assert args.args == ('kubectl apply -f -',)
    assert args.kwargs == dict(
        input="payload",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        text=True,
        env=env
    )
