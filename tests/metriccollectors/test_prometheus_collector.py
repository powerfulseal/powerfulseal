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
from prometheus_client import REGISTRY

from powerfulseal.metriccollectors import PrometheusCollector
from powerfulseal.metriccollectors.collector import NODE_SOURCE, POD_SOURCE
from powerfulseal.metriccollectors.prometheus_collector import STATUS_SUCCESS, \
    STATUS_FAILURE, POD_KILLS_METRIC_NAME, NODE_STOPS_METRIC_NAME, \
    EXECUTE_FAILED_METRIC_NAME, FILTERED_TO_EMPTY_SET_METRIC_NAME, \
    PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME, MATCHED_TO_EMPTY_SET_METRIC_NAME
# noinspection PyUnresolvedReferences
from tests.fixtures import node_scenario, make_dummy_object
# noinspection PyUnresolvedReferences
from tests.fixtures import noop_scenario
# noinspection PyUnresolvedReferences
from tests.fixtures import pod_scenario


@pytest.fixture
def prometheus_noop_scenario(noop_scenario):
    noop_scenario.metric_collector = PrometheusCollector()
    return noop_scenario


@pytest.fixture
def prometheus_pod_scenario(pod_scenario):
    pod_scenario.metric_collector = PrometheusCollector()
    return pod_scenario


@pytest.fixture
def prometheus_node_scenario(node_scenario):
    node_scenario.metric_collector = PrometheusCollector()
    return node_scenario


def get_aggregated_sample_values(registry, name, labels=None):
    """
    Returns the aggregated value based on cases where all the labels specified
    match. Returns 0 if no values are found.

    The reason why REGISTRY.get_sample_value is not directly used is that the
    library function performs an equality on all the labels instead of only the
    labels provided.
    """
    labels = labels or {}
    total = 0
    for metric in registry.collect():
        for n, l, value in metric.samples:
            if n == name:
                # Ensure that all labels provided match
                matching = all(k in l and v == l[k] for _, (k, v) in enumerate(labels.items()))
                if matching:
                    total += value
    return total


def test_add_pod_killed_metric(prometheus_pod_scenario):
    prometheus_pod_scenario.schema = {
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

    prometheus_pod_scenario.executor.execute = magic_mock

    mock_item1 = MagicMock()
    mock_item1.container_ids = ["docker://container1"]
    mock_item1.namespace = "default"
    mock_item1.name = "testpod1"

    mock_item2 = MagicMock()
    mock_item2.container_ids = ["docker://container2"]
    mock_item2.namespace = "default"
    mock_item2.name = "testpod2"

    before = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert before == 0

    prometheus_pod_scenario.act([mock_item1, mock_item1, mock_item1, mock_item2])

    after_total = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert after_total == 4

    after_first = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS,
                                                                                        'namespace': 'default',
                                                                                        'name': 'testpod1'})
    assert after_first == 3

    after_second = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS,
                                                                                         'namespace': 'default',
                                                                                         'name': 'testpod2'})
    assert after_second == 1


def test_add_pod_kill_failed_metric(prometheus_pod_scenario):
    prometheus_pod_scenario.schema = {
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
    prometheus_pod_scenario.executor.execute = magic_mock

    mock_item1 = MagicMock()
    mock_item1.container_ids = ["docker://container1"]
    mock_item1.namespace = "default"
    mock_item1.name = "testpod1"

    mock_item2 = MagicMock()
    mock_item2.container_ids = ["docker://container2"]
    mock_item2.namespace = "default"
    mock_item2.name = "testpod2"

    before = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert before == 0

    prometheus_pod_scenario.act([mock_item1, mock_item1, mock_item1, mock_item2])

    after_total = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert after_total == 4

    after_first = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE,
                                                                                        'namespace': 'default',
                                                                                        'name': 'testpod1'})
    assert after_first == 3

    after_second = get_aggregated_sample_values(REGISTRY, POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE,
                                                                                         'namespace': 'default',
                                                                                         'name': 'testpod2'})
    assert after_second == 1


def test_add_node_stopped_metric(prometheus_node_scenario):
    prometheus_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }

    mock_item1 = MagicMock()
    mock_item1.id = "1"
    mock_item1.name = "node1"

    mock_item2 = MagicMock()
    mock_item2.id = "2"
    mock_item2.name = "node2"

    items = [mock_item1, mock_item2]

    before = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert before == 0

    prometheus_node_scenario.act(items)

    after_total = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert after_total == 2

    after_first = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS,
                                                                                         'id': '1',
                                                                                         'name': 'node1'})
    assert after_first == 1

    after_second = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS,
                                                                                          'id': '2',
                                                                                          'name': 'node2'})
    assert after_second == 1


def test_add_node_stop_failed_metric(prometheus_node_scenario):
    prometheus_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }
    method = getattr(prometheus_node_scenario.driver, "stop")
    method.side_effect = Exception("something bad")

    mock_item1 = MagicMock()
    mock_item1.id = "1"
    mock_item1.name = "node1"

    mock_item2 = MagicMock()
    mock_item2.id = "2"
    mock_item2.name = "node2"

    items = [mock_item1, mock_item2]

    before = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert before == 0

    prometheus_node_scenario.act(items)

    after_total = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert after_total == 2

    after_first = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE,
                                                                                         'id': '1',
                                                                                         'name': 'node1'})
    assert after_first == 1

    after_second = get_aggregated_sample_values(REGISTRY, NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE,
                                                                                          'id': '2',
                                                                                          'name': 'node2'})
    assert after_second == 1


def test_add_execute_failed_metric(prometheus_node_scenario):
    prometheus_node_scenario.schema = {
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

    prometheus_node_scenario.executor.execute = magic_mock

    mock_item = MagicMock()
    mock_item.id = '1'
    mock_item.name = 'node1'
    items = [mock_item]

    before = get_aggregated_sample_values(REGISTRY, EXECUTE_FAILED_METRIC_NAME)
    assert before == 0

    prometheus_node_scenario.act(items)

    after = get_aggregated_sample_values(REGISTRY, EXECUTE_FAILED_METRIC_NAME, labels={'id': '1', 'name': 'node1'})
    assert after == 1


def test_add_filtered_to_empty_set_metric(prometheus_noop_scenario):
    before = REGISTRY.get_sample_value(FILTERED_TO_EMPTY_SET_METRIC_NAME)
    assert before == 0

    prometheus_noop_scenario.execute()

    after = REGISTRY.get_sample_value(FILTERED_TO_EMPTY_SET_METRIC_NAME)
    assert after == 1


def test_add_probability_filter_passed_no_nodes_metric(prometheus_noop_scenario):
    """
    Ensures that add_probability_filter_passed_no_nodes_metric is called when
    the filter decides to pass no nodes based on a probability
    """
    assert prometheus_noop_scenario.name == "test scenario"
    random.seed(6)  # make the tests deterministic
    candidates = [make_dummy_object()]

    before = REGISTRY.get_sample_value(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME)
    assert before == 0

    criterion = {"probabilityPassAll": 0.00000001}
    prometheus_noop_scenario.filter_probability(candidates, criterion)

    after = REGISTRY.get_sample_value(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME)
    assert after == 1


def test_add_matched_to_empty_set_metric(prometheus_node_scenario, prometheus_pod_scenario):
    prometheus_node_scenario.schema = {
        "match": [
            {
                "namespace": {
                    "name": "non-existent"
                }
            }
        ]
    }

    before = get_aggregated_sample_values(REGISTRY, MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert before == 0

    prometheus_node_scenario.match()

    after = get_aggregated_sample_values(REGISTRY, MATCHED_TO_EMPTY_SET_METRIC_NAME, labels={'source': NODE_SOURCE})
    assert after == 1

    prometheus_pod_scenario.schema = {
        "match": [
            {
                "namespace": {
                    "name": "non-existent"
                }
            }
        ]
    }

    before = get_aggregated_sample_values(REGISTRY, MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert before == 1

    prometheus_pod_scenario.match()

    after = get_aggregated_sample_values(REGISTRY, MATCHED_TO_EMPTY_SET_METRIC_NAME, labels={'source': POD_SOURCE})
    assert after == 1

    after_total = get_aggregated_sample_values(REGISTRY, MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert after_total == 2
