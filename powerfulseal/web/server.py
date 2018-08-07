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
import threading
import time
from threading import Lock

import jsonschema
import yaml
from flask import Flask, jsonify, request
from flask_cors import CORS

from powerfulseal.policy import PolicyRunner
from powerfulseal.policy.node_scenario import NodeScenario
from powerfulseal.policy.pod_scenario import POD_KILL_CMD_TEMPLATE, PodScenario
# Flask instance and routes
from powerfulseal.web.constants import *

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Singleton instance of the server
server_state = None


@app.route('/api/policy', methods=['GET', 'PUT'])
def policy_actions():
    if request.method == 'GET':
        # GET request: returns a JSON representation of the policy file
        policy = server_state.get_policy()

        # Format node scenario output for JSON output
        nodeScenarios = []
        for policyScenario in policy.get('nodeScenarios', []):
            outputScenario = DEFAULT_OUTPUT_NODE_SCENARIO
            outputScenario['name'] = policyScenario['name']

            # Process matchers
            for matcherItem in policyScenario.get('match', []):
                outputScenario['matchers'].append(matcherItem['property'])

            # Process filters
            for filterItem in policyScenario.get('filters', []):
                # In the schema, filter items are represented by an object with a single item

                # Process property filters
                if 'property' in filterItem:
                    outputScenario['filters'].append(filterItem['property'])

                # Process time of execution filters
                if 'dayTime' in filterItem:
                    for dayOfWeek in POLICY_DAYS_OF_WEEK:
                        outputScenario['dayOfWeek'][dayOfWeek] = \
                            dayOfWeek in filterItem['dayTime']['onlyDays']
                    outputScenario['startTime'] = filterItem['dayTime']['startTime']
                    outputScenario['endTime'] = filterItem['dayTime']['endTime']

                # Process random sample filters
                if 'randomSample' in filterItem:
                    if 'size' in filterItem['randomSample']:
                        # The default scenario's other keys must not be modified or else the front-end
                        # will missed keys which are being watched
                        outputScenario['randomSample']['type'] = RandomSampleType.SIZE,
                        outputScenario['randomSample']['size'] = filterItem['randomSample']['size']
                    elif 'ratio' in filterItem['randomSample']:
                        outputScenario['randomSample']['type'] = RandomSampleType.RATIO
                        outputScenario['randomSample']['ratio'] = filterItem['randomSample']['ratio']

                # Process probability pass all filters
                if 'probability' in filterItem:
                    outputScenario['probabilityPassAll']['isEnabled'] = True
                    outputScenario['probabilityPassAll']['probability'] = \
                        filterItem['probability']['probabilityPassAll']

            # Process actions
            for actionItem in policyScenario.get('actions', []):
                if 'stop' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.STOP,
                        'params': [{
                            'name': k,
                            'value': v,
                        } for (k, v) in actionItem['stop']]
                    })
                elif 'start' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.START,
                        'params': []
                    })
                elif 'wait' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.WAIT,
                        'params': [
                            {
                                'name': 'seconds',
                                'value': actionItem['wait']['seconds']
                            }
                        ]
                    })
                elif 'execute' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.EXECUTE,
                        'params': [
                            {
                                'name': 'cmd',
                                'value': actionItem['execute']['cmd']
                            }
                        ]
                    })

            nodeScenarios.append(outputScenario)

        # Format pod scenario output for JSON output
        podScenarios = []
        for policyScenario in policy.get('podScenarios', []):
            outputScenario = DEFAULT_OUTPUT_POD_SCENARIO
            outputScenario['name'] = policyScenario['name']

            # Process matchers
            for matcherItem in policyScenario.get('match', []):
                if 'namespace' in matcherItem:
                    outputScenario['matchers'].append({
                        'type': PodMatcherTypes.NAMESPACE,
                        'params': [{
                            'name': k,
                            'value': v
                        } for (k, v) in matcherItem['namespace']]
                    })
                elif 'deployment' in matcherItem:
                    outputScenario['matchers'].append({
                        'type': PodMatcherTypes.DEPLOYMENT,
                        'params': [{
                            'name': k,
                            'value': v
                        } for (k, v) in matcherItem['deployment']]
                    })
                elif 'labels' in matcherItem:
                    outputScenario['matchers'].append({
                        'type': PodMatcherTypes.LABELS,
                        'params': [{
                            'name': k,
                            'value': v,
                        } for (k, v) in matcherItem['labels']]
                    })

            # Process filters
            for filterItem in policyScenario.get('filters', []):
                # Process property filters
                if 'property' in filterItem:
                    outputScenario['filters'].append(filterItem['property'])

                # Process time of execution filters
                if 'dayTime' in filterItem:
                    for dayOfWeek in POLICY_DAYS_OF_WEEK:
                        outputScenario['dayOfWeek'][dayOfWeek] = \
                            dayOfWeek in filterItem['dayTime']['onlyDays']
                    outputScenario['startTime'] = filterItem['dayTime']['startTime']
                    outputScenario['endTime'] = filterItem['dayTime']['endTime']

                # Process random sample filters
                if 'randomSample' in filterItem:
                    if 'size' in filterItem['randomSample']:
                        # The default scenario's other keys must not be modified or else the front-end
                        # will missed keys which are being watched
                        outputScenario['randomSample']['type'] = RandomSampleType.SIZE,
                        outputScenario['randomSample']['size'] = filterItem['randomSample']['size']
                    elif 'ratio' in filterItem['randomSample']:
                        outputScenario['randomSample']['type'] = RandomSampleType.RATIO
                        outputScenario['randomSample']['ratio'] = filterItem['randomSample']['ratio']

                # Process probability pass all filters
                if 'probability' in filterItem:
                    outputScenario['probabilityPassAll']['isEnabled'] = True
                    outputScenario['probabilityPassAll']['probability'] = \
                        filterItem['probability']['probabilityPassAll']

            # Process actions
            for actionItem in policyScenario.get('actions', []):
                if 'kill' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.STOP,
                        'params': [{
                            'name': k,
                            'value': v,
                        } for (k, v) in actionItem['kill']]
                    })
                elif 'wait' in actionItem:
                    outputScenario['actions'].append({
                        'type': ActionType.WAIT,
                        'params': [
                            {
                                'name': 'seconds',
                                'value': actionItem['wait']['seconds']
                            }
                        ]
                    })

            podScenarios.append(outputScenario)

        return jsonify({
            'config': policy.get('config', {
                'minSecondsBetweenRuns': 0,
                'maxSecondsBetweenRuns': 300,
            }),
            'nodeScenarios': nodeScenarios,
            'podScenarios': podScenarios
        })
    elif request.method == 'PUT':
        # PUT request: modify a policy
        modified_policy = request.get_json().get('policy', None)
        if modified_policy is None:
            return jsonify({'error': 'Policy field missing'}), 400

        if not PolicyRunner.is_policy_valid(modified_policy):
            return jsonify({'error': 'Policy not valid'}), 400

        try:
            server_state.update_policy(modified_policy)
        except IOError:
            return jsonify({'error': 'Unable to overwrite policy file'}), 500

        return jsonify({}), 200

    return jsonify({}), 501


@app.route('/api/autonomous-mode', methods=['GET', 'POST'])
def autonomousMode():
    """
    GET: Gets the state of autonomous mode
    POST: Sets the state of autonomous mode (state is either start or stop)
    """
    if request.method == 'GET':
        return jsonify({'isStarted': server_state.is_policy_runner_running()})
    elif request.method == 'POST':
        params = request.get_json()
        action = params.get('action', None)
        if action is None:
            return jsonify({'error': 'Action field missing'}), 400

        if action not in ['start', 'stop']:
            return jsonify({'error': 'Action field must either be \'start\' or \'stop\''}), 400

        try:
            if action == 'start':
                if server_state.is_policy_runner_running():
                    return jsonify({'error': 'Policy runner already running'}), 412
                server_state.start_policy_runner()
            else:
                if not server_state.is_policy_runner_running():
                    return jsonify({'error': 'Policy runner already stopped'}), 412
                server_state.stop_policy_runner()
        except RuntimeError:
            return jsonify({'error': 'Policy runner is in an inconsistent state'}), 500

        return jsonify({})

    return jsonify({}), 501


@app.route('/api/logs')
def logs():
    """
    Retrieves the application logs
    """
    # Logs can be retrieves from the offset inclusive (e.g., if the offset is 3,
    # then return from index three (or fourth item in the list) inclusive [3:])
    offset = request.args.get('offset', default=0, type=int)

    if offset < 0:
        return jsonify({'error': 'Offset cannot be negative'}), 400

    with server_state.lock:
        if len(server_state.logs) < offset + 1:
            return jsonify({'logs': []})
        return jsonify({'logs': server_state.logs[offset:]})


@app.route('/api/items')
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


@app.route('/api/nodes', methods=['POST'])
def update_nodes():
    """
    Starts or stops a node identified by its IP address
    :return:
    """
    params = request.get_json()
    action = params.get('action', None)
    ip = params.get('ip', None)
    if action is None or ip is None:
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

    return jsonify({'error': 'Node IP address not found'}), 404


@app.route('/api/pods', methods=['POST'])
def update_pods():
    """
    Kills or force kills a pod by its UID field. Force kills if `is_forced` parameter
    is the string `true`.
    :return:
    """
    params = request.get_json()
    is_forced = params.get('isForced', False) in [True, 'true', '1', 1]
    uid = params.get('uid', None)
    if uid is None:
        return jsonify({'error': 'uid field missing'}), 400

    for pod in server_state.get_pods():
        if pod.uid == uid:
            is_action_successful = server_state.kill_pod(pod, is_forced)
            if is_action_successful:
                return jsonify({}), 200
            else:
                return jsonify({'error': 'Action on pod failed'}, 500)

    return jsonify({'error': 'Pod UID not found'}), 404


def start_server(host, port):
    app.run(host=host, port=port)


class ThreadedPolicyRunner(threading.Thread):
    def __init__(self, policy, inventory, k8s_inventory, driver, executor, stop_event, logger=None):
        super().__init__()
        config = policy.get("config", {})
        self.wait_min = config.get("minSecondsBetweenRuns", 0)
        self.wait_max = config.get("maxSecondsBetweenRuns", 300)

        self.node_scenarios = [
            NodeScenario(
                name=item.get("name"),
                schema=item,
                inventory=inventory,
                driver=driver,
                executor=executor,
            )
            for item in policy.get("nodeScenarios", [])
        ]

        self.pod_scenarios = [
            PodScenario(
                name=item.get("name"),
                schema=item,
                inventory=inventory,
                k8s_inventory=k8s_inventory,
                executor=executor,
            )
            for item in policy.get("podScenarios", [])
        ]

        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.driver = driver
        self.executor = executor
        self.logger = logger or logging.getLogger(__name__)

        self.stop_event = stop_event
        self.stop_event.clear()

    def run(self):
        while not self.stop_event.is_set():
            try:
                for scenario in self.node_scenarios:
                    scenario.execute()
                for scenario in self.pod_scenarios:
                    scenario.execute()
            except Exception as e:
                logging.error(e)
                self.stop()

            # Repeatedly check whether the stop event has been set in order to
            # prevent blocking the main thread while it waits for the thread to
            # join after stopping
            sleep_time = int(random.uniform(self.wait_min, self.wait_max))
            self.logger.debug("Sleeping for %s seconds", sleep_time)
            while sleep_time > 0 and not self.stop_event.is_set():
                time.sleep(1)
                sleep_time -= 1

            self.inventory.sync()

    def stop(self):
        self.stop_event.set()


class ServerState:
    def __init__(self, policy, inventory, k8s_inventory, driver, executor, policy_path, logger=None):
        # server_state must be accessed in a global context as Flask works within
        # a module level scope. As a result, there is no intuitive way for Flask
        # API endpoints to access the server state without first making the server
        # state a global singleton variable which Flask can directly access.
        global server_state
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
        # where race conditions could occur.
        self.lock = Lock()

        # Contains an instance of ThreadedPolicyRunner which is only set once
        # autonomous mode is started and cleared once it is stopped.
        # The threading.Event has to be in the main thread so the state of it can
        # be read while the policy runner thread blocks (e.g., sleeps).
        self.policy_runner = None
        self.policy_runner_stop_event = threading.Event()

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

    def is_policy_runner_running(self):
        with self.lock:
            return self.policy_runner is not None and not self.policy_runner_stop_event.is_set()

    def start_policy_runner(self):
        with self.lock:
            if self.policy_runner is not None and not self.policy_runner_stop_event.is_set():
                raise RuntimeError('Policy runner is already running')

            self.policy_runner = ThreadedPolicyRunner(self.policy, self.inventory,
                                                      self.k8s_inventory, self.driver,
                                                      self.executor, self.policy_runner_stop_event)
            self.policy_runner.start()

    def stop_policy_runner(self):
        with self.lock:
            if self.policy_runner is None or self.policy_runner_stop_event.is_set():
                raise RuntimeError('Policy runner is already stopped')

            self.policy_runner.stop()
            self.policy_runner.join()
            self.policy_runner = None


class ServerStateLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        with server_state.lock:
            server_state.logs.append({
                'timestamp': record.created,
                'level': record.levelname,
                'message': record.getMessage()
            })
