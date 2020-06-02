
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
from tests.fixtures import pod_scenario
from tests.fixtures import make_dummy_object


def test_matching_namespace(pod_scenario):
    a, b = make_dummy_object(), make_dummy_object()
    pod_scenario.schema = {
        "matches": [
            {
                "namespace": "something",
            },
        ]
    }
    pod_scenario.k8s_inventory.find_pods = MagicMock(return_value=[a, b])
    matched = pod_scenario.match()
    assert matched == list(set([a, b]))
    assert pod_scenario.k8s_inventory.find_pods.call_args[1] == {"namespace": "something"}

def test_matching_deployment(pod_scenario):
    a, b = make_dummy_object(), make_dummy_object()
    pod_scenario.schema = {
        "matches": [
            {
                "deployment": {
                    "name": "lol",
                    "namespace": "something",
                }
            },
        ]
    }
    pod_scenario.k8s_inventory.find_pods = MagicMock(return_value=[a, b])
    matched = pod_scenario.match()
    assert matched == list(set([a, b]))
    assert pod_scenario.k8s_inventory.find_pods.call_args[1] == {
        "deployment_name": "lol",
        "namespace": "something"
    }

def test_matching_labels(pod_scenario):
    a, b = make_dummy_object(), make_dummy_object()
    pod_scenario.schema = {
        "matches": [
            {
                "labels": {
                    "selector": "yes=true",
                    "namespace": "something",
                }
            },
        ]
    }
    pod_scenario.k8s_inventory.find_pods = MagicMock(return_value=[a, b])
    matched = pod_scenario.match()
    assert matched == list(set([a, b]))
    assert pod_scenario.k8s_inventory.find_pods.call_args[1] == {
        "selector": "yes=true",
        "namespace": "something"
    }


@pytest.mark.parametrize("should_force", [
    (True,),
    (False,)
])
def test_kills_correctly_with_force(pod_scenario, should_force):
    pod_scenario.schema = {
        "actions": [
            {
                "kill": {
                    "force": should_force
                }
            },
        ]
    }
    mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 1
        },
    })
    pod_scenario.executor.execute = mock
    mock_item1 = MagicMock()
    mock_item1.container_ids = ["docker://container1"]
    mock_item2 = MagicMock()
    mock_item2.container_ids = ["docker://container1"]
    items = [mock_item1, mock_item2]
    pod_scenario.act(items)
    assert mock.call_count == 2
    template = "sudo docker kill -s {signal} {container_id}"
    for i, call in enumerate(mock.call_args_list):
        args, kwargs = call
        cmd = template.format(
            signal="SIGKILL" if should_force else "SIGTERM",
            container_id=items[i].container_ids[0].replace("docker://","")
        )
        assert args[0] == cmd


@pytest.mark.parametrize("prob", [
    0.3,
    0.1,
    0.5,
    0.9
])
def test_kills_with_probability(pod_scenario, prob):
    random.seed(12)
    sample = 10000

    pod_scenario.schema = {
        "actions": [
            {
                "kill": {
                    "probability": prob,
                }
            },
        ]
    }
    mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 0
        },
    })
    pod_scenario.executor.execute = mock
    mock_item1 = MagicMock()
    mock_item1.container_ids = ["docker://container1"]
    items = [mock_item1]

    for _ in range(sample):
        pod_scenario.act(items)

    actual_prob = float(mock.call_count / len(items)) / sample
    assert (actual_prob == pytest.approx(prob, 0.05))


def test_doesnt_kill_when_cant_find_node(pod_scenario):
    pod_scenario.schema = {
        "actions": [
            {
                "kill": {
                    "force": True
                }
            },
        ]
    }
    pod_scenario.inventory.get_node_by_ip = MagicMock(return_value=None)
    pod_scenario.logger = MagicMock()
    mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 1
        },
    })
    pod_scenario.executor.execute = mock
    pod_scenario.executor.logger = MagicMock()
    mock_item1 = MagicMock()
    mock_item2 = MagicMock()
    items = [mock_item1, mock_item2]
    pod_scenario.act(items)
    assert mock.call_count == 0
    assert pod_scenario.executor.logger.info.call_args[0] == ("Node not found for pod: %s", items[1])
