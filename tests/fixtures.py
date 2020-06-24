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

from powerfulseal.policy.action_kubectl import ActionKubectl
from powerfulseal.policy.action_probe_http import ActionProbeHTTP
from powerfulseal.policy.action_nodes import ActionNodes
from powerfulseal.policy.action_pods import ActionPods
from powerfulseal.policy.action_nodes_pods import ActionNodesPods
from powerfulseal.execute import SSHExecutor


# Common fixtures
class Dummy():
    pass

def make_dummy_object():
    return Dummy()

@pytest.fixture
def dummy_object():
    return make_dummy_object()


# ActionNodesPods fixtures
@pytest.fixture
def noop_scenario():
    scenario = ActionNodesPods(
        name="test scenario",
        schema={}
    )
    scenario.match = MagicMock(return_value=[])
    scenario.filter = MagicMock(return_value=[])
    scenario.act = MagicMock()
    return scenario


@pytest.fixture
def no_filtered_items_scenario():
    scenario = ActionNodesPods(
        name="test scenario",
        schema={}
    )
    matched_items = [ make_dummy_object() ]
    scenario.match = MagicMock(return_value=matched_items)
    scenario.filter = MagicMock(return_value=[])
    scenario.act = MagicMock()
    return scenario


# Pod ActionNodesPods Fixtures
EXAMPLE_POD_SCHEMA = {
    "matches": [
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
    executor = SSHExecutor()
    return ActionPods(
        name="test scenario",
        schema=EXAMPLE_POD_SCHEMA,
        inventory=inventory,
        k8s_inventory=k8s_inventory,
        executor=executor,
    )


# Node ActionNodesPods Fixtures
EXAMPLE_NODE_SCHEMA = {
    "matches": [
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
    return ActionNodes(
        name="test scenario",
        schema=EXAMPLE_NODE_SCHEMA,
        inventory=inventory,
        driver=driver,
        executor=executor,
    )


@pytest.fixture
def action_kubectl():
    logger = MagicMock()
    return ActionKubectl(
        name="test kubectl action",
        schema=dict(
            action="apply",
            payload="---\n"
        ),
        logger=logger,
    )


@pytest.fixture
def action_probe_http():
    logger = MagicMock()
    k8s_inventory = MagicMock()
    return ActionProbeHTTP(
        name="test probe http action",
        schema=dict(
            target=dict(
                url="http://example.com"
            )
        ),
        k8s_inventory=k8s_inventory,
        logger=logger,
    )
