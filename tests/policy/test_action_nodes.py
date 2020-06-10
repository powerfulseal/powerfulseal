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
from mock import MagicMock

# noinspection PyUnresolvedReferences
from tests.fixtures import node_scenario
from tests.fixtures import make_dummy_object


def test_matching_matches(node_scenario):
    a, b = make_dummy_object(), make_dummy_object()
    a.attr = "a - this should match"
    b.attr = "b - this won't"
    node_scenario.schema = {
        "matches": [
            {
                "property": {
                    "name": "attr",
                    "value": "a.*"
                }
            },
        ]
    }
    node_scenario.inventory.find_nodes = MagicMock(return_value=[a, b])
    matched = node_scenario.match()
    assert matched == [a]


def test_matching_returns_things_once_if_multimatch(node_scenario):
    a, b = make_dummy_object(), make_dummy_object()
    a.attr = "a - this should match"
    b.attr = "b - this won't"
    node_scenario.schema = {
        "matches": [
            {
                "property": {
                    "name": "attr",
                    "value": "a.*"
                }
            },
            {
                "property": {
                    "name": "attr",
                    "value": ".*"
                }
            },
        ]
    }
    node_scenario.inventory.find_nodes = MagicMock(return_value=[a, b])
    matched = node_scenario.match()
    assert len(matched) == 2
    assert a in matched
    assert b in matched


@pytest.mark.parametrize("attr", [
    "start",
    "stop"
])
def test_calls_start_on_act(node_scenario, attr):
    node_scenario.schema = {
        "actions": [
            {
                attr: {
                }
            },
        ],
    }
    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item, mock_item]
    node_scenario.act(items)
    method = getattr(node_scenario.driver, attr)
    assert method.call_count == 2
    for i, call in enumerate(method.call_args_list):
        args, kwargs = call
        assert args[0] is items[i]


@pytest.mark.parametrize("attr", [
    "start",
    "stop"
])
def test_calls_start_on_act_raising_exception_dont_bubble(node_scenario, attr):
    node_scenario.schema = {
        "actions": [
            {
                attr: {
                }
            },
        ],
    }
    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item, mock_item]
    method = getattr(node_scenario.driver, attr)
    method.side_effect = Exception("something bad")
    node_scenario.logger = MagicMock()
    node_scenario.act(items)
    assert method.call_count == 2
    for i, call in enumerate(method.call_args_list):
        args, kwargs = call
        assert args[0] is items[i]
    assert node_scenario.logger.exception.call_count == 2


def test_action_execute_called_correctly(node_scenario):
    node_scenario.schema = {
        "actions": [
            {
                "execute": {
                    "cmd": "echo lol",
                }
            },
        ]
    }
    mock = MagicMock(return_value={
        "some ip": {
            "ret_code": 1
        },
    })
    node_scenario.executor.execute = mock
    mock_item = MagicMock()
    mock_item.uid = '1'
    mock_item.name = 'node1'
    items = [mock_item, mock_item]
    node_scenario.act(items)
    assert mock.call_count == 2
    for i, call in enumerate(mock.call_args_list):
        args, kwargs = call
        assert args[0] == "echo lol"
        assert kwargs["nodes"] == [items[i]]

def test_action_stop_creates_cleanup_action(node_scenario):
    node_scenario.schema["actions"] = [
        dict(
            stop=dict(
                autoRestart=True
            )
        )
    ]
    mock_item = MagicMock()
    node_scenario.act([mock_item])
    cleanup = node_scenario.get_cleanup_actions()
    assert len(cleanup) == 1
    assert cleanup[0] is not node_scenario
    assert cleanup[0].schema is not node_scenario.schema
    assert cleanup[0].schema != node_scenario.schema
    assert cleanup[0].schema.get("matches") == node_scenario.schema.get("matches")
    assert cleanup[0].schema.get("filters") == [{
        "property": {
            "name": "state",
            "value": "DOWN"
        }
    }]
    assert "start" in cleanup[0].schema["actions"][0]


def test_action_stop_doesnt_create_cleanup_action(node_scenario):
    node_scenario.schema["actions"] = [
        dict(
            stop=dict(
                autoRestart=False
            )
        )
    ]
    mock_item = MagicMock()
    node_scenario.act([mock_item])
    assert node_scenario.get_cleanup_actions() == []
