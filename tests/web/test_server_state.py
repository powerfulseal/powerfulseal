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
import time

import pkg_resources
from mock import mock, mock_open, MagicMock

from powerfulseal.execute import RemoteExecutor
from powerfulseal.node import NodeInventory, Node
from powerfulseal.policy import PolicyRunner
from powerfulseal.web.server import ServerState


def test_is_policy_valid_validates():
    valid_policy_path = pkg_resources.resource_filename("tests.policy", "example_config.yml")
    valid_policy = PolicyRunner.load_file(valid_policy_path)
    invalid_policy = {
        'config': {
            'minSecondsBetweenRuns': 'invalid'
        }
    }

    server_state = ServerState(valid_policy, None, None, None, None, None, None, None)
    assert server_state.is_policy_valid()

    server_state = ServerState(invalid_policy, None, None, None, None, None, None, None)
    assert not server_state.is_policy_valid()


def test_update_policy():
    test_path = 'test.yml'
    new_policy = {'test': 'test'}
    server_state = ServerState({}, None, None, None, None, None, None, test_path)

    m = mock_open()
    with mock.patch('powerfulseal.web.server.open', m, create=True):
        server_state.update_policy(new_policy)

    m.assert_called_once_with(test_path, 'w')
    assert server_state.policy == new_policy


def test_kill_pod():
    server_state = ServerState(None, NodeInventory(None), None, None, RemoteExecutor(), None, None, None)

    # Patch action of getting nodes to execute kill command on
    test_node = Node(1)
    get_node_by_ip_mock = MagicMock(return_value=test_node)
    server_state.inventory.get_node_by_ip = get_node_by_ip_mock

    # Patch action of choosing container
    execute_mock = MagicMock()
    server_state.executor.execute = execute_mock

    mock_pod = MagicMock()
    mock_pod.container_ids = ["docker://container1"]

    server_state.kill_pod(mock_pod, True)
    execute_mock.assert_called_once_with("sudo docker kill -s SIGKILL container1", nodes=[test_node])


def test_policy_runner_lifecycle():
    """
    Integration test which starts, checks status, and stops the policy runner
    """
    policy = {
        'config': {
            'minSecondsBetweenRuns': 0,
            'maxSecondsBetweenRuns': 2
        },
        'nodeScenarios': [
            {
                'name': 'Node Test'
            }
        ],
        'podScenarios': [
            {
                'name': 'Pod Test'
            }
        ]
    }
    test_inventory = MagicMock()
    test_inventory.sync = MagicMock(return_value=None)

    server_state = ServerState(policy, test_inventory, None, None, RemoteExecutor(), None, None, None)
    assert server_state.is_policy_runner_running() is False

    server_state.start_policy_runner()
    time.sleep(1)
    assert server_state.is_policy_runner_running() is True

    server_state.stop_policy_runner()
    time.sleep(1)
    assert server_state.is_policy_runner_running() is False
