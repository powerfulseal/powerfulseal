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
import time

from powerfulseal.policy.pod_scenario import POD_KILL_CMD_TEMPLATE

MIN_AGGRESSIVENESS = 1
MAX_AGGRESSIVENESS = 5


class DemoRunner:
    """
    Kills pods based on CPU core usage and memory usage to demonstrate how chaos
    can be created by killing pods which are busy.

    The CPU and memory information is retrieved from Heapster. Then, pods are
    first sorted by their CPU usage and memory and killed based on filters.

    - Pods are first filtered based on what quintile they in: an aggressiveness of
    1 means that only the top 20% of sorted pods are considered; an aggressiveness of
    5 means that all nodes are considered.
    - Pods are then filtered based on a probability which corresponds to an
    aggressiveness level which is linearly scaled from 10% (1) to 80% (5).
    """

    HIGHEST_PROBABILITY = 0.8
    LOWEST_PROBABILITY = 0.1
    BASE_MINUTES = 10

    def __init__(self, inventory, k8s_inventory, driver, executor, metric_client,
                 min_seconds_between_runs=0, max_seconds_between_runs=300,
                 aggressiveness=MIN_AGGRESSIVENESS, logger=None, namespace=None):
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.driver = driver
        self.executor = executor
        self.min_seconds_between_runs = min_seconds_between_runs
        self.max_seconds_between_runs = max_seconds_between_runs
        self.aggressiveness = aggressiveness
        self.metric_client = metric_client
        self.logger = logger or logging.getLogger(__name__)
        self.namespace=None

    def run(self):
        while True:
            # Filter
            all_pods = self.k8s_inventory.find_pods(self.namespace)
            self.logger.info("Found %d pods" % len(all_pods))
            pods = self.filter_pods(self.fill_metrics(all_pods))
            self.logger.info("Filtered to %d pods" % len(pods))

            # Execute
            for pod in pods:
                self.kill_pod(pod)

            # Sleep and sync
            sleep_time = int(random.uniform(self.min_seconds_between_runs, self.max_seconds_between_runs))
            self.logger.info("Sleeping for %s seconds", sleep_time)
            time.sleep(sleep_time)
            self.inventory.sync()

    def kill_pod(self, pod):
        # Find node
        node = self.inventory.get_node_by_ip(pod.host_ip)
        if node is None:
            self.logger.info("Node not found for pod: %s", pod)
            return

        # Format command
        container_id = random.choice(pod.container_ids)
        cmd = POD_KILL_CMD_TEMPLATE.format(
            signal="SIGTERM",
            container_id=container_id.replace("docker://", ""),
        )

        # Execute command
        self.logger.info("Action execute '%s' on %r", cmd, pod)
        for value in self.executor.execute(cmd, nodes=[node]).values():
            if value["ret_code"] > 0:
                self.logger.info("Error return code: %s", value)

    def sort_pods(self, pods):
        return sorted(pods, key=lambda pod: (pod.metrics['cpu'], pod.metrics['memory']), reverse=True)

    def fill_metrics(self, pods):
        """
        Adds a metrics variable to each Pod variable in a list of pods. Retrieves
        the metrics from Heapster.
        """
        metrics = self.metric_client.get_pod_metrics()
        filled_pods = []
        for pod in pods:
            try:
                pod.metrics = metrics[pod.namespace][pod.name]
                filled_pods.append(pod)
            except (KeyError, ValueError):
                self.logger.error("Pod metrics missing for pod %s/%s - skipping" % (pod.namespace, pod.name))

        return filled_pods

    def filter_pods(self, pods):
        filters = [
            self.filter_top,
            self.filter_probability
        ]

        remaining_pods = pods
        for pod_filter in filters:
            remaining_pods = pod_filter(remaining_pods)

        return remaining_pods

    def filter_top(self, pods):
        num_pods = int(len(pods) * float(self.aggressiveness / float(MAX_AGGRESSIVENESS)))
        return pods[0:num_pods]

    def filter_probability(self, pods):
        boundary = self.LOWEST_PROBABILITY + \
                   ((self.HIGHEST_PROBABILITY - self.LOWEST_PROBABILITY) / (MAX_AGGRESSIVENESS - MIN_AGGRESSIVENESS)) * \
                   (self.aggressiveness - MIN_AGGRESSIVENESS)
        remaining_pods = []

        for pod in pods:
            p = random.random()
            if boundary >= p:
                remaining_pods.append(pod)

        return remaining_pods
