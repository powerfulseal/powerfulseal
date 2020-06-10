
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

from powerfulseal.metriccollectors.collector import NODE_SOURCE
from .action_nodes_pods import ActionNodesPods


class ActionNodes(ActionNodesPods):
    """ ActionNodess scenario handler.

        Adds matching for nodes and node-specific actions
    """

    def __init__(self, name, schema, inventory, driver,
                 executor, logger=None, metric_collector=None):
        ActionNodesPods.__init__(self, name, schema, logger=logger, metric_collector=metric_collector)
        self.inventory = inventory
        self.driver = driver
        self.executor = executor
        self.action_mapping = {
            "stop": self.action_stop,
            "start": self.action_start,
            "wait": self.action_wait,
            "execute": self.action_execute,
        }
        self.cleanup_actions = []

    def match(self):
        """ Makes a union of all the nodes matching any of the policy criteria.
        """
        self.inventory.sync()
        selected_nodes = set()
        criteria = self.schema.get("matches", [])
        for node in self.inventory.find_nodes():
            for criterion in criteria:
                match = criterion.get("property")
                if self.match_property(node, match):
                    self.logger.debug("Matching %r", node)
                    selected_nodes.add(node)
        if len(selected_nodes) == 0:
            self.metric_collector.add_matched_to_empty_set_metric(NODE_SOURCE)
        return list(selected_nodes)

    def action_start(self, items, params):
        """ Action to start a node.
        """
        success = True
        for item in items:
            self.logger.info("Action start on %r", item)
            try:
                self.driver.start(item)
            except:
                self.logger.exception("Error starting the machine")
                success = False
        return success

    def action_stop(self, items, params):
        """ Action to stop a node.
        """
        auto_restart = params.get("autoRestart", True)
        success = True
        for item in items:
            self.logger.info("Action stop on %r", item)
            try:
                self.driver.stop(item)
                if auto_restart:
                    schema = dict()
                    schema["matches"] = self.schema.get("matches", {})
                    schema["filters"] = [
                        dict(property=dict(
                            name="state",
                            value="DOWN"
                        ))
                    ]
                    schema["actions"] = [
                        dict(start=dict())
                    ]
                    start = ActionNodes(
                        name=self.name,
                        schema=schema,
                        inventory=self.inventory,
                        driver=self.driver,
                        executor=self.executor
                    )
                    self.cleanup_actions.append(start)
                self.metric_collector.add_node_stopped_metric(item)
            except:
                self.metric_collector.add_node_stop_failed_metric(item)
                self.logger.exception("Error stopping the machine")
                success = False
        return success

    def action_execute(self, items, params):
        """ Executes arbitrary code on the node.
        """
        cmd = params.get("cmd", "hostname")
        success = True
        for item in items:
            self.logger.info("Action execute '%s' on %r", cmd, item)
            for value in self.executor.execute(
                cmd, nodes=[item]
            ).values():
                if value["ret_code"] > 0:
                    self.logger.info("Error return code: %s", value)
                    self.metric_collector.add_execute_failed_metric(item)
                    success = False
        return success

    def get_cleanup_actions(self):
        return self.cleanup_actions
