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
from mock import mock, MagicMock

from powerfulseal.metriccollectors import DatadogCollector

from powerfulseal.metriccollectors.collector import NODE_SOURCE, POD_SOURCE

# noinspection PyUnresolvedReferences
from tests.fixtures import noop_scenario
# noinspection PyUnresolvedReferences
from tests.fixtures import pod_scenario
# noinspection PyUnresolvedReferences
from tests.fixtures import node_scenario
from tests.fixtures import make_dummy_object

@pytest.fixture
def datadog_noop_scenario(noop_scenario):
    noop_scenario.metric_collector = DatadogCollector()
    return noop_scenario


@pytest.fixture
def datadog_pod_scenario(pod_scenario):
    pod_scenario.metric_collector = DatadogCollector()
    return pod_scenario

@pytest.fixture
def datadog_node_scenario(node_scenario):
    node_scenario.metric_collector = DatadogCollector()
    return node_scenario

def test_add_pod_killed_metric(datadog_pod_scenario):
    datadog_pod_scenario.schema = {
        "actions": [
            {
                "kill": {
                    "force": False
                }
            },
        ]
    }
    magic_mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 0
        },
    })

    datadog_pod_scenario.executor.execute = magic_mock
    
    mock_item = MagicMock()
    mock_item.container_ids = ["docker://container1"]
    mock_item.namespace = "default"
    mock_item.name = "test_pod1"

    items = [mock_item]

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_pod_killed_metric') as metric_function:
        metric_function.assert_not_called()
        datadog_pod_scenario.act(items)
        metric_function.assert_called_with(mock_item)

def test_add_pod_kill_failed_metric(datadog_pod_scenario):
    datadog_pod_scenario.schema = {
        "actions": [
            {
                "kill": {
                    "force": False
                }
            },
        ]
    }
    magic_mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 1
        },
    })
    datadog_pod_scenario.executor.execute = magic_mock
    mock_item = MagicMock()
    mock_item.container_ids = ["docker://container1"]
    mock_item.namespace = "default"
    mock_item.name = "test_pod1"

    items = [mock_item]

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_pod_kill_failed_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_pod_scenario.act(items)
        metric_function.assert_called_with(mock_item)


def test_add_node_stopped_metric(datadog_node_scenario):
    datadog_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }

    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item]

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_node_stopped_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_node_scenario.act(items)
        metric_function.assert_called_once_with(mock_item)


def test_add_node_stop_failed_metric(datadog_node_scenario):
    datadog_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }

    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item]

    method = getattr(datadog_node_scenario.driver, "stop")
    method.side_effect = Exception("something bad")

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_node_stop_failed_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_node_scenario.act(items)
        metric_function.assert_called_once_with(mock_item)


def test_add_execute_failed_metric(datadog_node_scenario):
    datadog_node_scenario.schema = {
        "actions": [
            {
                "execute": {
                    "cmd": "test",
                }
            },
        ]
    }
    magic_mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 1
        },
    })
    datadog_node_scenario.executor.execute = magic_mock

    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item]

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_execute_failed_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_node_scenario.act(items)
        metric_function.assert_called_once_with(mock_item)


def test_add_filtered_to_empty_set_metric(datadog_noop_scenario):
    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_filtered_to_empty_set_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_noop_scenario.execute()
        metric_function.assert_called()


def test_add_probability_filter_passed_no_nodes_metric(datadog_noop_scenario):
    """
    Ensures that add_probability_filter_passed_no_nodes_metric is called when
    the filter decides to pass no nodes based on a probability
    """
    assert datadog_noop_scenario.name == "test scenario"
    random.seed(6)  # make the tests deterministic
    candidates = [make_dummy_object()]

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_probability_filter_passed_no_nodes_filter') \
            as metric_function:
        # Ensure metric is not added when nodes are all passed
        criterion = {"probabilityPassAll": 1}
        datadog_noop_scenario.filter_probability(candidates, criterion)
        metric_function.assert_not_called()

        # Ensure metric is added when nodes are not passed
        criterion = {"probabilityPassAll": 0.00000001}
        datadog_noop_scenario.filter_probability(candidates, criterion)
        metric_function.assert_called()


def test_add_matched_to_empty_set_metric(datadog_node_scenario, datadog_pod_scenario):
    datadog_node_scenario.schema = {
        "match": [
            {
                "namespace": {
                    "name": "non-existent"
                }
            }
        ]
    }

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_matched_to_empty_set_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_node_scenario.match()
        metric_function.assert_called_once_with(NODE_SOURCE)

    datadog_pod_scenario.schema = {
        "match": [
            {
                "namespace": {
                    "name": "non-existent"
                }
            }
        ]
    }

    with mock.patch('powerfulseal.metriccollectors.DatadogCollector.add_matched_to_empty_set_metric') \
            as metric_function:
        metric_function.assert_not_called()
        datadog_pod_scenario.match()
        metric_function.assert_called_once_with(POD_SOURCE)
