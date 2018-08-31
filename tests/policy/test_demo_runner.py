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
import random

import pytest
from mock import MagicMock

from powerfulseal.execute import RemoteExecutor
from powerfulseal.node import NodeInventory, Node
from powerfulseal.policy.demo_runner import DemoRunner


def test_kill_pod():
    demo_runner = DemoRunner(NodeInventory(None), None, None, RemoteExecutor(), None)

    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    demo_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    demo_runner.executor.execute = execute_mock

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]
    demo_runner.kill_pod(mock_pod)

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]
    demo_runner.kill_pod(mock_pod)

    execute_mock.assert_called_with("sudo docker kill -s SIGTERM container1", nodes=[test_node])


def test_sort_pods():
    pod_1 = MagicMock()
    pod_1.metrics = {
        'cpu': 10,
        'memory': 0
    }

    pod_2 = MagicMock()
    pod_2.metrics = {
        'cpu': 5,
        'memory': 3
    }

    pod_3 = MagicMock()
    pod_3.metrics = {
        'cpu': 5,
        'memory': 2
    }

    demo_runner = DemoRunner(NodeInventory(None), None, None, RemoteExecutor(), None)
    assert demo_runner.sort_pods([pod_2, pod_3, pod_1]) == [pod_1, pod_2, pod_3]


def test_filter_top():
    first_quintile_runner = DemoRunner(None, None, None, None, None, aggressiveness=1)
    assert len(first_quintile_runner.filter_top([MagicMock() for _ in range(5)])) == 1
    assert len(first_quintile_runner.filter_top([MagicMock() for _ in range(10)])) == 2
    assert len(first_quintile_runner.filter_top([MagicMock() for _ in range(3)])) == 0
    
    third_quintile_runner = DemoRunner(None, None, None, None, None, aggressiveness=3)
    assert len(third_quintile_runner.filter_top([MagicMock() for _ in range(5)])) == 3
    assert len(third_quintile_runner.filter_top([MagicMock() for _ in range(10)])) == 6
    assert len(third_quintile_runner.filter_top([MagicMock() for _ in range(3)])) == 1

    all_runner = DemoRunner(NodeInventory(None), None, None, None, None, aggressiveness=5)
    assert len(all_runner.filter_top([MagicMock() for _ in range(5)])) == 5
    assert len(all_runner.filter_top([MagicMock() for _ in range(10)])) == 10
    assert len(all_runner.filter_top([MagicMock() for _ in range(3)])) == 3


@pytest.mark.parametrize('case', [
    (1, 0.1),
    (2, 0.275),
    (3, 0.45),
    (4, 0.625),
    (5, 0.8)
])
def test_filter_probability(case):
    random.seed(12)
    sample = 1000

    runner = DemoRunner(None, None, None, None, None, aggressiveness=case[0])
    filtered_items = runner.filter_probability([MagicMock() for _ in range(sample)])
    assert pytest.approx(case[1] * sample, 1) == len(filtered_items)

