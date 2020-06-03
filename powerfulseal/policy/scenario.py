
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


import logging

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_nodes import ActionNodes
from .action_pods import ActionPods
from .action_kubectl import ActionKubectl


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
        self.logger = logger or logging.getLogger(__name__ + "." + name)
        self.metric_collector = metric_collector or StdoutCollector()
        self.action_mapping = dict(
            nodeAction=self.action_nodes,
            podAction=self.action_pods,
            kubectl=self.action_kubectl,
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
                    ret = action_method(schema=step.get(action_name))
                    if not ret:
                        self.logger.warning("Step returned failure %s", step)
                        return False
        self.logger.info("Scenario '%s' finished", self.name)
        self.cleanup()
        self.logger.info("Scenario '%s' finished", self.name)
        return True

    def cleanup(self):
        for action in self.cleanup_list:
            self.execute_action(action)

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
        )
        return self.execute_action(action)
