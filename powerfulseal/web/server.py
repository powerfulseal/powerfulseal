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

import logging
import random
from threading import Lock

import jsonschema
import yaml
from flask import Flask, jsonify, request

from powerfulseal.policy import PolicyRunner
from powerfulseal.policy.pod_scenario import POD_KILL_CMD_TEMPLATE

# Flask instance and routes
app = Flask(__name__)

# Singleton instance of the server
server_state = None


@app.route('/policy', methods=['GET', 'PUT'])
def policy_actions():
    if request.method == 'GET':
        # GET request: returns a JSON representation of the policy file
        policy = server_state.get_policy()
        return jsonify({
            'config': policy.get('config', []),
            'nodeScenarios': policy.get('nodeScenarios', []),
            'podScenarios': policy.get('podScenarios', [])
        })
    elif request.method == 'PUT':
        # POST request: modify a policy
        try:
            modified_policy = request.form['policy']
        except KeyError:
            return jsonify({'error': 'Policy field missing'}), 400

        if not PolicyRunner.is_policy_valid(modified_policy):
            return jsonify({'error': 'Policy not valid'}), 400

        try:
            server_state.update_policy(modified_policy)
        except IOError:
            return jsonify({'error': 'Unable to overwrite policy file'}), 500

        return jsonify({}), 200

    return jsonify({}), 501


@app.route('/autonomous-mode', methods=['POST'])
def autonomousMode():
    """
    Sets the state of autonomous mode (state is either start or stop)
    """
    pass


@app.route('/logs')
def logs():
    """
    Retrieves the application logs
    """
    pass


@app.route('/items')
def items():
    """
    Gets a list of nodes and pods
    """

    nodes = [{
        'id': node.id,
        'name': node.name,
        'ip': node.ip,
        'az': node.az,
        'groups': node.groups,
        'no': node.no,
        'state': node.state
    } for node in server_state.get_nodes()]

    pods = [{
        'name': pod.name,
        'namespace': pod.namespace,
        'num': pod.num,
        'uid': pod.uid,
        'host_ip': pod.host_ip,
        'ip': pod.ip,
        'container_ids': pod.container_ids,
        'state': pod.state,
        'labels': pod.labels
    } for pod in server_state.get_pods()]

    return jsonify({'nodes': nodes, 'pods': pods})


@app.route('/nodes', methods=['POST'])
def nodes():
    """
    Starts or stops a node identified by its IP address
    :return:
    """
    try:
        action = request.form['action']
        ip = request.form['ip']
    except KeyError:
        return jsonify({'error': 'Action/IP address fields missing'}), 400

    if action not in ['start', 'stop']:
        return jsonify({'error': 'Invalid action'}), 400

    for node in server_state.get_nodes():
        if node.ip == ip:
            if action == 'start':
                is_action_successful = server_state.start_node(node)
            else:
                is_action_successful = server_state.stop_node(node)

            if is_action_successful:
                return jsonify({}), 200
            else:
                return jsonify({'error': 'Action on node failed'}, 500)

    return jsonify({'error': 'Node IP address not found'}), 400


@app.route('/pods', methods=['POST'])
def pods():
    """
    Kills or force kills a pod by its UID field. Force kills if `is_forced` parameter
    is the string `true`.
    :return:
    """
    try:
        is_forced = request.form['is_forced'] == 'true'
        uid = request.form['uid']
    except KeyError:
        return jsonify({'error': 'is_forced/uid fields missing'}), 400

    for pod in server_state.get_pods():
        if pod.uid == uid:
            is_action_successful = server_state.kill_pod(pod, is_forced)
            if is_action_successful:
                return jsonify({}), 200
            else:
                return jsonify({'error': 'Action on pod failed'}, 500)

    return jsonify({'error': 'Pod UID not found'}), 400


def start_server(host, port):
    app.run(host=host, port=port)


class ServerState:
    def __init__(self, policy, inventory, k8s_inventory, driver, executor, policy_path, logger=None):
        # server_state must be accessed in a global context as Flask works within
        # a module level scope. As a result, there is no intuitive way for Flask
        # API endpoints to access the server state without first making the server
        # state a global singleton variable which Flask can directly access.
        global server_state
        if server_state is not None:
            print("Unable to create singleton server instance. Exiting.")
            exit(-1)
        server_state = self

        self.policy = policy
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.driver = driver
        self.executor = executor
        self.policy_path = policy_path

        self.logger = logger or logging.getLogger(__name__)
        self.logs = []

        # Due to concurrent requests, it is safer to acquire locks on variables
        # where race conditions could occur
        self.lock = Lock()

    def is_policy_valid(self):
        """
        Checks whether the specified policy is valid depending on the schema
        file used in the PolicyRunner class
        """
        schema = PolicyRunner.get_schema()
        try:
            jsonschema.validate(self.policy, schema)
        except jsonschema.ValidationError:
            return False
        return True

    def get_policy(self):
        with self.lock:
            return self.policy

    def update_policy(self, policy):
        """
        :except IOError
        """
        with self.lock:
            with open(self.policy_path, 'w') as f:
                f.write(yaml.dump(policy, default_flow_style=False))
            self.policy = policy

    def get_nodes(self):
        return self.inventory.get_all_nodes()

    def get_pods(self):
        return self.k8s_inventory.get_all_pods()

    def start_node(self, node):
        """
        Starts a node. Returns true on success and false on failure.
        """
        try:
            self.driver.start(node)
            return True
        except:
            self.logger.error("Error starting the machine")
            return False

    def stop_node(self, node):
        """
        Stops a node. Returns true on success and false on failure.
        """
        try:
            self.driver.stop(node)
            return True
        except:
            self.logger.error("Error stopping the machine")
            return False

    def kill_pod(self, pod, is_forced):
        """
        Kills a pod. Returns true on success and false on failure.
        """
        # Get node to execute kill command on
        node = self.inventory.get_node_by_ip(pod.host_ip)
        if node is None:
            return False

        # Format kill command
        signal = "SIGKILL" if is_forced else "SIGTERM"
        container_id = random.choice(pod.container_ids)
        cmd = POD_KILL_CMD_TEMPLATE.format(
            signal=signal,
            container_id=container_id.replace("docker://", ""),
        )

        # Send kill command
        for value in self.executor.execute(cmd, nodes=[node]).values():
            if value["ret_code"] > 0:
                return False

        return True


class ServerStateLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        with server_state.lock:
            server_state.logs.append({
                'timestamp': record.created,
                'level': record.levelname,
                'message': record.msg
            })
