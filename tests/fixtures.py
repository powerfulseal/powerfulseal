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
import pytest
from mock import MagicMock

from powerfulseal.policy.node_scenario import NodeScenario
from powerfulseal.policy.pod_scenario import PodScenario
from powerfulseal.policy.scenario import Scenario


# Common fixtures
class Dummy():
    pass

def make_dummy_object():
    return Dummy()

@pytest.fixture
def dummy_object():
    return make_dummy_object()


# Scenario fixtures
class NoopScenario(Scenario):

    def match(self):
        return []

    def act(self, items):
        pass


@pytest.fixture
def noop_scenario():
    return NoopScenario(
        name="test scenario",
        schema={}
    )


# Pod Scenario Fixtures
EXAMPLE_POD_SCHEMA = {
    "match": [
        {
            "property": {
                "name": "attr",
                "value": "a.*"
            }
        },
    ]
}


@pytest.fixture
def pod_scenario():
    inventory = MagicMock()
    k8s_inventory = MagicMock()
    executor = MagicMock()
    return PodScenario(
        name="test scenario",
        schema=EXAMPLE_POD_SCHEMA,
        inventory=inventory,
        k8s_inventory=k8s_inventory,
        executor=executor,
    )


# Node Scenario Fixtures
EXAMPLE_NODE_SCHEMA = {
    "match": [
        {
            "property": {
                "name": "attr",
                "value": "a.*"
            }
        },
    ]
}


@pytest.fixture
def node_scenario():
    inventory = MagicMock()
    driver = MagicMock()
    executor = MagicMock()
    return NodeScenario(
        name="test scenario",
        schema=EXAMPLE_NODE_SCHEMA,
        inventory=inventory,
        driver=driver,
        executor=executor,
    )
