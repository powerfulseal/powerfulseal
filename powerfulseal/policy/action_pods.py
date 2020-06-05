
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
import re

from powerfulseal.metriccollectors.collector import POD_SOURCE
from .action_nodes_pods import ActionNodesPods


class ActionPods(ActionNodesPods):
    """ Pod scenario handler.

        Adds matching for k8s-specific things and pod-specific actions
    """

    def __init__(self, name, schema, inventory, k8s_inventory, executor,
                 logger=None, metric_collector=None):
        ActionNodesPods.__init__(self, name, schema, logger=logger, metric_collector=metric_collector)
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.executor = executor
        self.action_mapping = {
            "wait": self.action_wait,
            "kill": self.action_kill,
            "checkPodCount": self.action_check_pod_count,
            "checkPodState": self.action_check_pod_state,
        }

    def match(self):
        """ Makes a union of all the pods matching any of the policy criteria.
        """
        mapping = {
            "namespace": self.match_namespace,
            "deployment": self.match_deployment,
            "labels": self.match_labels,
        }
        selected = set()
        criteria = self.schema.get("matches", [])
        self.logger.debug("Criteria %r ",criteria)
        for criterion in criteria:
            for action_name, action_method in mapping.items():
                if action_name in criterion:
                    self.logger.info("Matching %r %r", action_name, criterion)
                    params = criterion.get(action_name)
                    for pod in action_method(params):
                        self.logger.debug("Matching %r", pod)
                        selected.add(pod)
        if len(selected) == 0:
            self.metric_collector.add_matched_to_empty_set_metric(POD_SOURCE)
        return list(selected)

    def match_namespace(self, param):
        """ Matches pods for a namespace
        """
        namespace = param
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

    def action_kill(self, pods, params):
        """ Kills a pod by executing a docker kill on one of the containers or pod delete
        """
        probability = params.get("probability", 1)
        force = params.get("force", True)
        signal = "SIGKILL" if force else "SIGTERM"
        success = True
        for pod in pods:
            if probability < random.random():
                self.logger.info("Pod got lucky - not killing")
            else:
                ret_val = True
                try:
                    ret_val = self.executor.kill_pod(pod, self.inventory, signal)
                except:
                    self.logger.exception("Exception while killing pod")
                    ret_val = False
                # update the metrics
                if ret_val:
                    self.metric_collector.add_pod_killed_metric(pod)
                    self.logger.info("Pod killed: %s", pod)
                else:
                    self.metric_collector.add_pod_kill_failed_metric(pod)
                    self.logger.error("Pod NOT killed: %s", pod)
                    success = False
        return success

    def action_check_pod_count(self, pods, params):
        """
            Checks that the count of pods equals the desired count.
        """
        count = int(params.get("count"))
        if len(pods) != count:
            self.logger.error("Expected %d pods, got %d", count, len(pods))
            return False
        return True

    def action_check_pod_state(self, pods, params):
        """
            Checks that all the pods are in desired state.
        """
        state = params.get("state")
        success = True
        for pod in pods:
            if not self.match_property(
                candidate=pod,
                criterion=dict(
                    name="state",
                    value=state,
                )
            ):
                self.logger.error("Expected pod in state '%s', got '%s' (%r)", state, pod.state, pod)
                success = False
        return success
