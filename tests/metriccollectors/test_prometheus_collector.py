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
from powerfulseal.metriccollectors.prometheus_collector import STATUS_SUCCESS, \
    STATUS_FAILURE, POD_KILLS_METRIC_NAME, NODE_STOPS_METRIC_NAME, \
    EXECUTE_FAILED_METRIC_NAME, FILTERED_TO_EMPTY_SET_METRIC_NAME, \
    PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME, MATCHED_TO_EMPTY_SET_METRIC_NAME
# noinspection PyUnresolvedReferences
from tests.fixtures import node_scenario, dummy_object
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
    mock_item2 = MagicMock()
    mock_item2.container_ids = ["docker://container2"]
    items = [mock_item1, mock_item2]

    before = REGISTRY.get_sample_value(POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert (before is None)

    prometheus_pod_scenario.act(items)

    after = REGISTRY.get_sample_value(POD_KILLS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert (after == 2)


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
    mock_item2 = MagicMock()
    mock_item2.container_ids = ["docker://container2"]
    items = [mock_item1, mock_item2]

    before = REGISTRY.get_sample_value(POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert (before is None)

    prometheus_pod_scenario.act(items)

    after = REGISTRY.get_sample_value(POD_KILLS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert (after == 2)


def test_add_node_stopped_metric(prometheus_node_scenario):
    prometheus_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }
    items = [dict(), dict()]

    before = REGISTRY.get_sample_value(NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert (before is None)

    prometheus_node_scenario.act(items)

    after = REGISTRY.get_sample_value(NODE_STOPS_METRIC_NAME, labels={'status': STATUS_SUCCESS})
    assert (after == 2)


def test_add_node_stop_failed_metric(prometheus_node_scenario):
    prometheus_node_scenario.schema = {
        "actions": [
            {
                "stop": {}
            },
        ],
    }
    items = [dict(), dict()]
    method = getattr(prometheus_node_scenario.driver, "stop")
    method.side_effect = Exception("something bad")

    before = REGISTRY.get_sample_value(NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert (before is None)

    prometheus_node_scenario.act(items)

    after = REGISTRY.get_sample_value(NODE_STOPS_METRIC_NAME, labels={'status': STATUS_FAILURE})
    assert (after == 2)


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
    items = [dict(), dict()]

    before = REGISTRY.get_sample_value(EXECUTE_FAILED_METRIC_NAME)
    assert (before == 0)

    prometheus_node_scenario.act(items)

    after = REGISTRY.get_sample_value(EXECUTE_FAILED_METRIC_NAME)
    assert (after == 2)


def test_add_filtered_to_empty_set_metric(prometheus_noop_scenario):
    before = REGISTRY.get_sample_value(FILTERED_TO_EMPTY_SET_METRIC_NAME)
    assert (before == 0)

    prometheus_noop_scenario.execute()

    after = REGISTRY.get_sample_value(FILTERED_TO_EMPTY_SET_METRIC_NAME)
    assert (after == 1)


def test_add_probability_filter_passed_no_nodes_metric(prometheus_noop_scenario):
    """
    Ensures that add_probability_filter_passed_no_nodes_metric is called when
    the filter decides to pass no nodes based on a probability
    """
    assert (prometheus_noop_scenario.name == "test scenario")
    random.seed(6)  # make the tests deterministic
    candidates = [dummy_object()]

    before = REGISTRY.get_sample_value(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME)
    assert (before == 0)

    criterion = {"probabilityPassAll": 0.00000001}
    prometheus_noop_scenario.filter_probability(candidates, criterion)

    after = REGISTRY.get_sample_value(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME)
    assert (after == 1)


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

    before = REGISTRY.get_sample_value(MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert (before == 0)

    prometheus_node_scenario.match()

    after = REGISTRY.get_sample_value(MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert (after == 1)

    prometheus_pod_scenario.schema = {
        "match": [
            {
                "namespace": {
                    "name": "non-existent"
                }
            }
        ]
    }

    before = REGISTRY.get_sample_value(MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert (before == 1)

    prometheus_pod_scenario.match()

    before = REGISTRY.get_sample_value(MATCHED_TO_EMPTY_SET_METRIC_NAME)
    assert (before == 2)
