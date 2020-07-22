
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


import pytest
import pkg_resources
from mock import MagicMock
import mock

from powerfulseal.policy import PolicyRunner


def test_default_policy_validates():
    assert PolicyRunner.is_policy_valid(PolicyRunner.DEFAULT_POLICY)


def test_example_config_validates():
    filename = pkg_resources.resource_filename("tests.policy", "example_config.yml")
    policy = PolicyRunner.load_file(filename)
    assert PolicyRunner.is_policy_valid(policy)

crd_scenario_name = "test"

def get_scenarios_mock():
    return [{
        "name": crd_scenario_name,
        "steps": [
            {"podAction": {
                "matches": [{"labels": {"namespace": "powerfulseal-sandbox", "selector": "app=nginx"}}],
                "actions": [{"kill": {"probability": 1}}]
            }}
        ]
    }]

def test_parses_config_correctly(monkeypatch):
    with mock.patch('powerfulseal.k8s.k8s_client') as k8s_client:
        k8s_client.get_scenarios = get_scenarios_mock
        sleep_mock = MagicMock()
        monkeypatch.setattr("time.sleep", sleep_mock)
        filename = pkg_resources.resource_filename(
            "tests.policy", "example_config2.yml")
        runner = PolicyRunner(filename, k8s_client)
        policy = runner.read_policy()
        inventory = MagicMock()
        k8s_inventory = MagicMock()
        driver = MagicMock()
        executor = MagicMock()
        LOOPS = policy.get("config").get("runStrategy").get("runs")
        assert policy.get("scenarios")[1].get("name") == crd_scenario_name
        runner.run(inventory, k8s_inventory, driver, executor)
        assert sleep_mock.call_count == LOOPS
        for call in sleep_mock.call_args_list:
            args, _ = call
            assert 77 <= args[0] <= 78
