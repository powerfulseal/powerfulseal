
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

import time

from powerfulseal import makeLogger

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_nodes import ActionNodes
from .action_pods import ActionPods
from .action_kubectl import ActionKubectl
from .action_probe_http import ActionProbeHTTP
from .action_clone import ActionClone


class Scenario():
    """
        A Scenario represents a complete chaos engineering experiment.
    """

    def __init__(self, name, schema, inventory, k8s_inventory,
        driver, executor, logger=None, metric_collector=None):
        self.name = name
        self.schema = schema
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.executor = executor
        self.driver = driver
        self.logger = logger or makeLogger(__name__, name)
        self.metric_collector = metric_collector or StdoutCollector()
        self.action_mapping = dict(
            nodeAction=self.action_nodes,
            podAction=self.action_pods,
            kubectl=self.action_kubectl,
            probeHTTP=self.action_probe_http,
            wait=self.action_wait,
            clone=self.action_clone,
        )
        self.cleanup_list = []

    def execute(self):
        """
            Main entry point to starting a scenario.
        """
        steps = self.schema.get("steps", [])
        self.logger.info("Starting scenario '%s' (%d steps)", self.name, len(steps))
        for step in steps:
            for action_name, action_method in self.action_mapping.items():
                if action_name in step:
                    step_action = step.get(action_name)
                    ret = self.retry(step_action, action_method)
                    if not ret:
                        self.logger.warning("Step returned failure %s. Finishing scenario early", step)
                        self.metric_collector.add_scenario_counter_metric(self.name, False)
                        self.cleanup()
                        return False
        self.logger.info("Scenario finished")
        self.metric_collector.add_scenario_counter_metric(self.name, True)
        self.cleanup()
        return True

    def retry(self, step_action, action_method):
        ret = False
        if "retries" in step_action.keys():
            step_retry = step_action['retries']
            if "retriesTimeout" in step_retry.keys():
                final_timeout = step_retry.get('retriesTimeout', {}).get('timeout', 60)
                retry_sleep = step_retry.get('retriesTimeout', {}).get('sleep', 30)
                timer = 0
                while timer < final_timeout:
                    ret = action_method(schema=step_action)
                    if ret:
                        return ret
                    else:
                        self.logger.warning("Failure in action. Sleeping %s and retrying", retry_sleep)
                        #  wait a little
                        time.sleep(retry_sleep)
                        timer += retry_sleep
                self.logger.error("No more retries allowed. Failing step")
                return False

            elif 'retriesCount' in step_retry.keys():
                final_count = step_retry.get('retriesCount', {}).get('count', 1)
                retry_sleep = step_retry.get('retriesCount', {}).get('sleep', 30)
                counter = 0
                while counter < final_count:
                    ret = action_method(schema=step_action)
                    if ret:
                        return ret
                    else:
                        self.logger.warning("Failure in action. Sleeping %s and retrying", retry_sleep)
                        #  wait a little
                        time.sleep(retry_sleep)
                        counter += 1
                self.logger.error("No more retries allowed. Failing step")
                return False

        else:
            ret = action_method(schema=step_action)
        return ret

    def cleanup(self):
        if not self.cleanup_list:
            self.logger.debug("No cleanup needed")
            return
        self.logger.info("Cleanup started (%d items)", len(self.cleanup_list))
        for action in self.cleanup_list:
            action.execute()
        self.cleanup_list = []
        self.logger.info("Cleanup done")

    def execute_action(self, action):
        ret_val = action.execute()
        for action in action.get_cleanup_actions():
            self.cleanup_list.append(action)
        return ret_val

    def action_nodes(self, schema):
        action = ActionNodes(
            schema=schema,
            name=self.name,
            inventory=self.inventory,
            driver=self.driver,
            executor=self.executor,
        )
        return self.execute_action(action)

    def action_pods(self, schema):
        action = ActionPods(
            schema=schema,
            name=self.name,
            inventory=self.inventory,
            k8s_inventory=self.k8s_inventory,
            executor=self.executor,
        )
        return self.execute_action(action)

    def action_kubectl(self, schema):
        action = ActionKubectl(
            schema=schema,
            name=self.name,
            kube_config=self.k8s_inventory.k8s_client.kube_config,
        )
        return self.execute_action(action)

    def action_probe_http(self, schema):
        action = ActionProbeHTTP(
            schema=schema,
            name=self.name,
            k8s_inventory=self.k8s_inventory,
        )
        return self.execute_action(action)

    def action_wait(self, schema):
        """ Waits x seconds, according to the policy.
        """
        sleep_time = schema.get("seconds", 0.0)
        self.logger.info("Sleeping for %r seconds", sleep_time)
        time.sleep(sleep_time)
        return True

    def action_clone(self, schema):
        action = ActionClone(
            schema=schema,
            name=self.name,
            k8s_inventory=self.k8s_inventory,
        )
        return self.execute_action(action)
