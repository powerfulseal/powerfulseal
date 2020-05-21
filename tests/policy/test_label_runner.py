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

from powerfulseal.execute import SSHExecutor, KubernetesExecutor
from powerfulseal.node import NodeInventory, Node
from powerfulseal.policy.label_runner import LabelRunner
from powerfulseal.k8s.pod import Pod

def test_kill_pod_APIcalling():

    k8s_client_mock = MagicMock()
    label_runner = LabelRunner(NodeInventory(None), None, None, KubernetesExecutor(k8s_client_mock))

    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    label_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch k8s inventory
    k8s_inventory = MagicMock()
    label_runner.k8s_inventory = k8s_inventory

    # Patch action of choosing container
    label_runner.k8s_inventory.k8s_client = k8s_client_mock

    delete_pods_mock = MagicMock()
    label_runner.k8s_inventory.k8s_client.delete_pods = delete_pods_mock
    
    metric_collector = MagicMock()
    label_runner.metric_collector = metric_collector

    add_pod_killed_metric_mock = MagicMock()
    label_runner.metric_collector.add_pod_killed_metric = add_pod_killed_metric_mock

    mock_pod = Pod(name='test', namespace='test')
    mock_pod.container_ids = ["docker://container1"]
    label_runner.kill_pod(mock_pod)

    delete_pods_mock.assert_called_with([mock_pod])
    add_pod_killed_metric_mock.assert_called_with(mock_pod)


def test_kill_pod_SSHing():    
    label_runner = LabelRunner(NodeInventory(None), None, None, SSHExecutor())

    # patch metrics collector
    label_runner.metric_collector = MagicMock()

    # Patch action of switching to SSHing mode
    k8s_inventory = MagicMock()
    label_runner.k8s_inventory = k8s_inventory
    
    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    label_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    label_runner.executor.execute = execute_mock

    mock_pod = Pod(name='test', namespace='test')
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {"seal/force-kill": "false"}
    label_runner.kill_pod(mock_pod)

    mock_pod = Pod(name='test', namespace='test')
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {}
    label_runner.kill_pod(mock_pod)

    execute_mock.assert_called_with("sudo docker kill -s SIGTERM container1", nodes=[test_node])


def test_kill_pod_forced_SSHing():
    label_runner = LabelRunner(NodeInventory(None), None, None, SSHExecutor())

    # patch metrics collector
    label_runner.metric_collector = MagicMock()

    # Patch action of switching to SSHing mode
    k8s_inventory = MagicMock()
    label_runner.k8s_inventory = k8s_inventory
    
    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    label_runner.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    label_runner.executor.execute = execute_mock

    mock_pod = Pod(name='test', namespace='test')
    mock_pod.container_ids = ["docker://container1"]
    mock_pod.labels = {"seal/force-kill": "true"}
    label_runner.kill_pod(mock_pod)
    execute_mock.assert_called_once_with("sudo docker kill -s SIGKILL container1", nodes=[test_node])


def test_filter_is_enabled():
    label_runner = LabelRunner(None, None, None, None)

    pods = [
        Pod(name='test', namespace='test', labels={'seal/enabled': 'true'}),
        Pod(name='test', namespace='test', labels={'seal/enabled': 'false'}),
        Pod(name='test', namespace='test', labels={'seal/enabled': 'asdf'}),
        Pod(name='test', namespace='test', labels={'bla': 'bla'}),
        Pod(name='test', namespace='test', annotations={'seal/enabled': 'true'}),
        Pod(name='test', namespace='test', annotations={'seal/enabled': 'false'}),
        Pod(name='test', namespace='test', annotations={'seal/enabled': 'true'}, labels={'seal/enabled': 'false'}),
        Pod(name='test', namespace='test', annotations={'seal/enabled': 'false'}, labels={'seal/enabled': 'true'})
    ]

    filtered_pods = label_runner.filter_is_enabled(pods)

    assert len(filtered_pods) is 3
    assert filtered_pods[0] is pods[0]
    assert filtered_pods[1] is pods[4]
    assert filtered_pods[2] is pods[7]

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
    pod = Pod(name='test', namespace='test')
    pod.labels = {'seal/kill-probability': str(proba)}

    agg_len = 0.0
    for _ in range(SAMPLES):
        agg_len += len(label_runner.filter_kill_probability([pod]))
    assert float(agg_len) / SAMPLES == pytest.approx(proba, 0.01)


def test_filter_day_time():
    label_runner = LabelRunner(None, None, None, None)

    pod = Pod(name="test", namespace="test")
    pod.labels = {
        "seal/start-time": "10-00-00",
        "seal/end-time": "17-30-00",
        "seal/days": "mon,tue,wed,thu,fri,sat,sun"
    }

    for day in range(7):
        now = datetime.now()
        # check that it works for all the days of the week, as specified above
        now.replace(day=day+1)
        # set the microseconds to 0, to pass the inclusive start
        now.replace(microsecond=0)
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
