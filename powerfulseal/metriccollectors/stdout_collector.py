
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


from powerfulseal import makeLogger
from powerfulseal.metriccollectors.collector import AbstractCollector

logger = makeLogger(__name__)


class StdoutCollector(AbstractCollector):
    """
        Passes metrics collected directly to stdout
    """

    def add_pod_killed_metric(self, pod):
        logger.debug("Pod killed - namespace: %s - name: %s", pod.namespace, pod.name)

    def add_pod_kill_failed_metric(self, pod):
        logger.debug("Pod killed - namespace: %s - name: %s", pod.namespace, pod.name)

    def add_node_stopped_metric(self, node):
        logger.debug("Node stopped - uid: %s - name: %s", node.id, node.name)

    def add_node_stop_failed_metric(self, node):
        logger.debug("Node stop failed - uid: %s - name: %s", node.id, node.name)

    def add_execute_failed_metric(self, node):
        logger.debug("Execute failed - uid: %s - name: %s", node.id, node.name)

    def add_filtered_to_empty_set_metric(self):
        logger.debug("Filtered to empty set")

    def add_probability_filter_passed_no_nodes_filter(self):
        logger.debug("Probability filter passed no nodes")

    def add_matched_to_empty_set_metric(self, source):
        logger.debug("Matched to empty set - source: %s", source)

    def add_scenario_counter_metric(self, name, result):
        logger.debug("Scenario %s result: %s", name, result)
