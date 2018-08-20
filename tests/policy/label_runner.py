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
from datetime import datetime

import pytest
from mock import MagicMock

from powerfulseal.execute import RemoteExecutor
from powerfulseal.node import NodeInventory, Node
from powerfulseal.policy.label_runner import LabelRunner


def test_kill_pod():
    label_runner = LabelRunner(NodeInventory(None), None, None, RemoteExecutor())

    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    label_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    label_runner.executor.execute = execute_mock

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {"seal/force-kill": "false"}
    label_runner.kill_pod(mock_pod)

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {}
    label_runner.kill_pod(mock_pod)

    execute_mock.assert_called_with("sudo docker kill -s SIGTERM container1", nodes=[test_node])


def test_kill_pod_forced():
    label_runner = LabelRunner(NodeInventory(None), None, None, RemoteExecutor())

    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    label_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    label_runner.executor.execute = execute_mock

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {"seal/force-kill": "true"}
    label_runner.kill_pod(mock_pod)
    execute_mock.assert_called_once_with("sudo docker kill -s SIGKILL container1", nodes=[test_node])


def test_filter_is_enabled():
    label_runner = LabelRunner(None, None, None, None)

    enabled_pod = MagicMock()
    enabled_pod.labels = {'seal/enabled': 'true'}
    disabled_pod_1 = MagicMock()
    disabled_pod_1.labels = {'seal/enabled': 'false'}
    disabled_pod_2 = MagicMock()
    disabled_pod_2.labels = {'seal/enabled': 'asdf'}
    disabled_pod_3 = MagicMock()
    disabled_pod_3.labels = {'bla': 'bla'}

    filtered_pods = label_runner.filter_is_enabled([enabled_pod, disabled_pod_1,
                                                    disabled_pod_2, disabled_pod_3])
    assert len(filtered_pods) is 1
    assert filtered_pods[0] == enabled_pod


@pytest.mark.parametrize("proba", [
    0.3,
    0.1,
    0.5,
    0.9
])
def test_filter_kill_probability(proba):
    random.seed(7)  # make the tests deterministic
    SAMPLES = 100000

    label_runner = LabelRunner(None, None, None, None)
    pod = MagicMock()
    pod.labels = {'seal/kill-probability': str(proba)}

    agg_len = 0.0
    for _ in range(SAMPLES):
        agg_len += len(label_runner.filter_kill_probability([pod]))
    assert float(agg_len) / SAMPLES == pytest.approx(proba, 0.01)


def test_filter_day_time():
    label_runner = LabelRunner(None, None, None, None)

    pod = MagicMock
    pod.labels = {
        "seal/start-time": "10-00-00",
        "seal/end-time": "17-30-00"
    }

    now = datetime.now()
    test_cases = [
        (now.replace(hour=8, minute=0, second=0), False, "far too early"),
        (now.replace(hour=9, minute=59, second=59), False, "just too early"),
        (now.replace(hour=10, minute=0, second=0), True, "inclusive start"),
        (now.replace(hour=13, minute=0, second=0), True, "within"),
        (now.replace(hour=17, minute=30, second=0), False, "exclusive end"),
        (now.replace(hour=17, minute=30, second=1), False, "just too late"),
        (now.replace(hour=20, minute=0, second=0), False, "far too late")
    ]

    for test_case in test_cases:
        assert (len(label_runner.filter_day_time([pod], test_case[0])) == 1) == test_case[1]


def test_get_integer_days_from_days_label():
    label_runner = LabelRunner(None, None, None, None)
    integer_days = label_runner.get_integer_days_from_days_label("mon,abc,tue,wed,thu,thur,fri,sat,sun,bla")
    assert integer_days == [0, 1, 2, 3, 4, 5, 6]


def test_process_time_label():
    label_runner = LabelRunner(None, None, None, None)

    with pytest.raises(ValueError) as _:
        label_runner.process_time_label("10-00-0")

    with pytest.raises(ValueError) as _:
        label_runner.process_time_label("-1-00-00")

    with pytest.raises(ValueError) as _:
        label_runner.process_time_label("24-00-00")

    assert (1, 22, 21) == label_runner.process_time_label("01-22-21")
