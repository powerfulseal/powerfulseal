
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
import pytest
from mock import MagicMock


# noinspection PyUnresolvedReferences
from tests.fixtures import action_kubectl


def test_creates_cleanup_action(action_kubectl):
    action_kubectl.schema["autoDelete"] = True
    action_kubectl.execute()
    cleanup = action_kubectl.get_cleanup_actions()
    assert len(cleanup) == 1
    job = cleanup[0]
    assert job is not action_kubectl
    assert job.schema is not action_kubectl.schema
    assert job.schema["payload"] == action_kubectl.schema["payload"]
    assert job.schema["action"] == "delete"
    assert job.schema["autoDelete"] == False


def test_doesnt_create_cleanup_action(action_kubectl):
    action_kubectl.schema["autoDelete"] = False
    action_kubectl.execute()
    assert action_kubectl.get_cleanup_actions() == []