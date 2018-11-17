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
import json
from threading import Lock

import pkg_resources
import pytest
from mock import mock, MagicMock

from powerfulseal.execute import RemoteExecutor
from powerfulseal.k8s import Pod
from powerfulseal.node import Node, NodeState
from powerfulseal.policy import PolicyRunner
from powerfulseal.web import server
from powerfulseal.web.formatter import PolicyFormatter
from powerfulseal.web.server import ServerState


@pytest.fixture
def client():
    client = server.app.test_client()
    yield client


def test_node_state_values_are_expected():
    """
    The API depends on the integer values of the NodeState enum. If these values
    are changed, then the API spec and front-end need to reflect these changes.
    """
    assert NodeState.UNKNOWN == 1
    assert NodeState.UP == 2
    assert NodeState.DOWN == 3
    assert len(NodeState) == 3


def test_autonomous_mode_integration(client):
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

    # Autonomous mode has not yet started
    result = client.get('/api/autonomous-mode')
    assert json.loads(result.data.decode("utf-8"))['isStarted'] is False

    # Autonomous mode has not yet started so it cannot be stopped
    result = client.post('/api/autonomous-mode', data=json.dumps({
        'action': 'stop'
    }), content_type='application/json')
    assert result.status_code == 412

    # Start autonomous mode
    result = client.post('/api/autonomous-mode', data=json.dumps({
        'action': 'start'
    }), content_type='application/json')
    assert result.status_code == 200

    # Autonomous mode has started
    result = client.get('/api/autonomous-mode')
    assert json.loads(result.data.decode("utf-8"))['isStarted'] is True

    # Autonomous mode has started so it cannot be started
    result = client.post('/api/autonomous-mode', data=json.dumps({
        'action': 'start'
    }), content_type='application/json')
    assert result.status_code == 412

    # Stop autonomous mode
    result = client.post('/api/autonomous-mode', data=json.dumps({
        'action': 'stop'
    }), content_type='application/json')
    assert result.status_code == 200

    # Autonomous mode has stopped
    result = client.get('/api/autonomous-mode')
    assert json.loads(result.data.decode("utf-8"))['isStarted'] is False


def test_get_policy_actions(client):
    server_state_mock = MagicMock()
    server_state_mock.get_policy = MagicMock(return_value={})
    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.get("/api/policy")
        assert json.loads(result.data.decode("utf-8")) == {
            'minSecondsBetweenRuns': 0,
            'maxSecondsBetweenRuns': 300,
            'nodeScenarios': [],
            'podScenarios': []
        }


def test_post_policy_actions(client):
    server_state_mock = MagicMock()

    valid_policy = {
        'minSecondsBetweenRuns': 0,
        'maxSecondsBetweenRuns': 300,
        'nodeScenarios': [],
        'podScenarios': []
    }

    invalid_policy = {
        'config': {
            'minSecondsBetweenRuns': 'invalid'
        }
    }

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.post("/api/policy", data=json.dumps({
            'policy': PolicyFormatter.output_policy(valid_policy)
        }), content_type='application/json')
        assert result.status_code == 200

        result = client.post("/api/policy", data=json.dumps({
            'policy': PolicyFormatter.output_policy(invalid_policy)
        }), content_type='application/json')
        assert result.status_code == 400


def test_put_policy_actions(client):
    server_state_mock = MagicMock()
    server_state_mock.update_policy = MagicMock()

    valid_policy_path = pkg_resources.resource_filename("tests.policy", "example_config.yml")
    valid_policy = PolicyRunner.load_file(valid_policy_path)

    invalid_policy = {
        'config': {
            'minSecondsBetweenRuns': 'invalid'
        }
    }

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.put("/api/policy", data=json.dumps({
            'policy': PolicyFormatter.output_policy(valid_policy)
        }), content_type='application/json')
        assert result.status_code == 200

        result = client.put("/api/policy", data=json.dumps({
            'policy': invalid_policy
        }), content_type='application/json')
        assert result.status_code == 400


def test_get_logs(client):
    # An instance of Lock will have to be created as there is no straightforward
    # way to mock a lock
    server_state_mock = MagicMock()
    server_state_mock.lock = Lock()

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        # Test case where an offset is not specified
        server_state_mock.logs = [str(i) for i in range(3)]
        result = client.get("/api/logs")
        assert json.loads(result.data.decode("utf-8"))['logs'] == [str(i) for i in range(3)]

        # Test case where offset is specified and correct result is given
        server_state_mock.logs = [str(i) for i in range(9)]
        result = client.get("/api/logs?offset=5")
        assert json.loads(result.data.decode("utf-8"))['logs'] == ['5', '6', '7', '8']

        # Test edge case where just within range
        server_state_mock.logs = [str(i) for i in range(9)]
        result = client.get("/api/logs?offset=8")
        assert json.loads(result.data.decode("utf-8"))['logs'] == ['8']

        # Test edge case where just outside range
        server_state_mock.logs = [str(i) for i in range(9)]
        result = client.get("/api/logs?offset=9")
        assert json.loads(result.data.decode("utf-8"))['logs'] == []

        # Test case where offset is negative
        # Test edge case where just within range
        server_state_mock.logs = [str(i) for i in range(9)]
        result = client.get("/api/logs?offset=-1")
        assert result.status_code == 400


def test_get_nodes(client):
    server_state_mock = MagicMock()

    test_node = Node(1, name='a',
                     ip='0.0.0.0',
                     az='A',
                     groups='a',
                     no=1,
                     state=NodeState.UP)
    server_state_mock.get_nodes = MagicMock(return_value=[test_node])

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.get('/api/nodes')
        server_state_mock.get_nodes.assert_called_once()

        data = json.loads(result.data.decode("utf-8"))
        assert len(data['nodes']) == 1

        # Ensure that the state is converted to an integer
        assert isinstance(data['nodes'][0]['state'], int)
        assert data['nodes'][0]['state'] == NodeState.UP


def test_get_pods(client):
    server_state_mock = MagicMock()

    test_pod = Pod('a',
                   namespace='a',
                   num=1,
                   uid='a',
                   host_ip='0.0.0.0',
                   ip='0.0.0.0',
                   container_ids=['a'],
                   state=0,
                   labels=['a'])
    server_state_mock.get_pods = MagicMock(return_value=[test_pod])

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        # General case
        result = client.get('/api/pods')
        server_state_mock.get_pods.assert_called_once()

        data = json.loads(result.data.decode("utf-8"))
        assert len(data['pods']) == 1
        assert data['pods'][0]['num'] == 1

        # Case where namespace is empty
        result = client.get('/api/pods?namespace=')
        assert len(json.loads(result.data.decode("utf-8"))['pods']) == 1

        # Case where namespace matches the pod's namespace
        result = client.get('/api/pods?namespace=a')
        assert len(json.loads(result.data.decode("utf-8"))['pods']) == 1

        # Case where namespace is not the same as the pod's namespace
        result = client.get('/api/pods?namespace=b')
        assert len(json.loads(result.data.decode("utf-8"))['pods']) == 0


def test_update_nodes(client):
    server_state_mock = MagicMock()
    server_state_mock.start_node = MagicMock(return_value=True)
    server_state_mock.stop_node = MagicMock(return_value=True)

    test_node = Node(1, ip='0.0.0.0')
    server_state_mock.get_nodes = MagicMock(return_value=[test_node])

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.post('/api/nodes', data=json.dumps({
            'action': 'start',
            'ip': '0.0.0.0'
        }), content_type='application/json')
        assert result.status_code == 200
        assert server_state_mock.start_node.call_count == 1
        assert server_state_mock.stop_node.call_count == 0

        result = client.post('/api/nodes', data=json.dumps({
            'action': 'stop',
            'ip': '0.0.0.0'
        }), content_type='application/json')
        assert result.status_code == 200
        assert server_state_mock.start_node.call_count == 1
        assert server_state_mock.stop_node.call_count == 1


def test_update_pods(client):
    server_state_mock = MagicMock()

    test_pod = Pod('a', 'a', uid='1-1-1-1')
    server_state_mock.get_pods = MagicMock(return_value=[test_pod])
    server_state_mock.kill_pod = MagicMock(return_value=True)

    with mock.patch("powerfulseal.web.server.server_state", server_state_mock):
        result = client.post('/api/pods', data=json.dumps({
            'isForced': True,
            'uid': '1-1-1-1'
        }), content_type='application/json')
        assert result.status_code == 200
        server_state_mock.kill_pod.assert_called_once_with(test_pod, True)

        result = client.post('/api/pods', data=json.dumps({
            'uid': '1-1-1-1'
        }), content_type='application/json')
        assert result.status_code == 200
        server_state_mock.kill_pod.assert_called_with(test_pod, False)

        result = client.post('/api/pods', data=json.dumps({
            'isForced': False,
            'uid': '1-1-1-1'
        }), content_type='application/json')
        assert result.status_code == 200
        server_state_mock.kill_pod.assert_called_with(test_pod, False)
