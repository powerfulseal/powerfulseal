
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


import random

from powerfulseal.metriccollectors.collector import POD_SOURCE
from .scenario import Scenario


class PodScenario(Scenario):
    """ Pod scenario handler.

        Adds metching for k8s-specific things and pod-specific actions
    """

    def __init__(self, name, schema, inventory, k8s_inventory, executor,
                 logger=None, metric_collector=None):
        Scenario.__init__(self, name, schema, logger=logger, metric_collector=metric_collector)
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.executor = executor

    def match(self):
        """ Makes a union of all the pods matching any of the policy criteria.
        """
        mapping = {
            "namespace": self.match_namespace,
            "deployment": self.match_deployment,
            "labels": self.match_labels,
        }
        selected = set()
        criteria = self.schema.get("match", [])
        for criterion in criteria:
            for key, method in mapping.items():
                if key in criterion:
                    params = criterion.get(key)
                    for pod in method(params):
                        self.logger.debug("Matching %r", pod)
                        selected.add(pod)
        if len(selected) == 0:
            self.metric_collector.add_matched_to_empty_set_metric(POD_SOURCE)
        return list(selected)

    def match_namespace(self, params):
        """ Matches pods for a namespace
        """
        namespace = params.get("name")
        pods = self.k8s_inventory.find_pods(
            namespace=namespace,
        )
        self.logger.info("Matched %d pods in namespace %s", len(pods), namespace)
        return pods

    def match_deployment(self, params):
        """ Matches pods for a deployment
        """
        namespace = params.get("namespace")
        deployment_name = params.get("name")
        pods = self.k8s_inventory.find_pods(
            namespace=namespace,
            deployment_name=deployment_name,
        )
        self.logger.info("Matched %d pods for deploy %s in namespace %s",
                 len(pods), deployment_name, namespace
        )
        return pods

    def match_labels(self, params):
        """ Matches pods for a selector
        """
        namespace = params.get("namespace")
        selector = params.get("selector")
        pods = self.k8s_inventory.find_pods(
            namespace=namespace,
            selector=selector,
        )
        self.logger.info("Matched %d pods for selector %s in namespace %s",
                 len(pods), selector, namespace
        )
        return pods

    def action_kill(self, pod, params):
        """ Kills a pod by executing a docker kill on one of the containers or pod delete
        """
        probability = params.get("probability", 1)
        force = params.get("force", True)
        signal = "SIGKILL" if force else "SIGTERM"
        if probability >= random.random():
            # kill the pod
            success = None
            try:
                success = self.executor.kill_pod(pod, self.inventory, signal)
            except:
                success = False
                self.logger.exception("Exception while killing pod")
            # update the metrics
            if success:
                self.metric_collector.add_pod_killed_metric(pod)
            else:
                self.metric_collector.add_pod_kill_failed_metric(pod)
            return success
        else:
            self.logger.info("Pod got lucky - not killing")

    def act(self, items):
        """ Executes all the supported actions on the list of pods.
        """
        actions = self.schema.get("actions", [])
        mapping = {
            "wait": self.action_wait,
            "kill": self.action_kill,
        }
        return self.act_mapping(items, actions, mapping)

