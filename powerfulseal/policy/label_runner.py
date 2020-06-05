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
import random

import time
from datetime import datetime


class LabelRunner:
    """
    Matches labels of individual pods and kills them if appropriate.

    Labels supported:
    `seal/enabled`          either "true" or "false" (default: "false")
    `seal/force-kill`       either "true" or "false" (default: "false")
    `seal/kill-probability` a value between "0" and "1" inclusive (default: "1")
    `seal/days`             a comma-separated string consisting of "mon", "tue",
                            "wed", "thu", "fri", "sat", "sun" describing the
                            pod can be killed (default: "mon,tue,wed,thu,fri")
    `seal/start-time`       a value "HH-MM-SS" for the inclusive start boundary
                            of when a pod can be killed in the local timezone
                            (default: "10-00-00")
    `seal/end-time`         a value "HH-MM-SS" for the exclusive end boundary of
                            when a pod can be killed in the local timezone
                            (default: "17-30-00")
    """
    DEFAULT_DAYS_LABEL = "mon,tue,wed,thu,fri"
    DAY_STRING_TO_DATETIME = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4,
                              'sat': 5, 'sun': 6}

    def __init__(self, inventory, k8s_inventory, driver, executor,
                 min_seconds_between_runs=0, max_seconds_between_runs=300, logger=None,
                 namespace=None, metric_collector=None):
        self.inventory = inventory
        self.k8s_inventory = k8s_inventory
        self.driver = driver
        self.executor = executor
        self.min_seconds_between_runs = min_seconds_between_runs
        self.max_seconds_between_runs = max_seconds_between_runs
        self.logger = logger or makeLogger(__name__)
        self.namespace = namespace
        self.metric_collector = metric_collector

    def run(self):
        while True:
            # Filter
            app_pods_in_namespace = self.k8s_inventory.find_pods(self.namespace)
            self.logger.info("Found %d pods" % len(app_pods_in_namespace))
            pods = self.filter_pods(app_pods_in_namespace)
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
        # prep the arguments
        signal = "SIGTERM"
        if pod.get_label_or_annotation("seal/force-kill", "false") == "true":
            signal = "SIGKILL"
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
            self.logger.info("Pod killed: %s", pod)
        else:
            self.metric_collector.add_pod_kill_failed_metric(pod)
            self.logger.error("Pod NOT killed: %s", pod)
        return success

    def filter_pods(self, pods):
        filters = [
            self.filter_is_enabled,
            self.filter_day_time,
            self.filter_kill_probability
        ]

        remaining_pods = pods
        for pod_filter in filters:
            remaining_pods = pod_filter(remaining_pods)

        return remaining_pods

    def filter_is_enabled(self, pods):
        return list(filter(lambda pod: pod.get_label_or_annotation("seal/enabled", "false") == "true", pods))

    def filter_kill_probability(self, pods):
        remaining_pods = []
        for pod in pods:
            # Retrieve probability value, performing validation
            try:
                probability = float(pod.get_label_or_annotation("seal/kill-probability", "1"))
                if probability < 0 or probability > 1:
                    raise ValueError
            except ValueError:
                self.logger.warning("Invalid float value - skipping pod %s/%s" % (pod.namespace, pod.name))
                continue

            p = random.random()
            if probability < p:
                continue

            remaining_pods.append(pod)

        return remaining_pods

    def filter_day_time(self, pods, now=None):
        remaining_pods = []
        now = now or datetime.now()

        for pod in pods:
            # Filter on days
            days_label = pod.get_label_or_annotation("seal/days", self.DEFAULT_DAYS_LABEL)
            if now.weekday() not in self.get_integer_days_from_days_label(days_label):
                continue

            # Filter on start time
            start_time_label = pod.get_label_or_annotation("seal/start-time", "10-00-00")
            try:
                hours, minutes, seconds = self.process_time_label(start_time_label)
                start_time = now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
                if now < start_time:
                    continue
            except ValueError:
                self.logger("Invalid start time - skipping pod %s/%s" % (pod.namespace, pod.name))
                continue

            # Filter on end time
            end_time_label = pod.get_label_or_annotation("seal/end-time", "17-30-00")
            try:
                hours, minutes, seconds = self.process_time_label(end_time_label)
                end_time = now.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
                if now >= end_time:
                    continue
            except ValueError:
                self.logger("Invalid end time - skipping pod %s/%s" % (pod.namespace, pod.name))
                continue

            remaining_pods.append(pod)

        return remaining_pods

    def get_integer_days_from_days_label(self, label):
        """
        Returns a list of integer day of week values compatible with the datetime
        package representing the days which a pod can be killed
        """
        string_days = label.split(',')

        days = []
        for string_day in string_days:
            try:
                days.append(self.DAY_STRING_TO_DATETIME[string_day])
            except KeyError:
                self.logger.warning("Invalid day label encountered: %s" % string_day)

        return days

    def process_time_label(self, label):
        """
        Validates and return a 3-tuple of hour, minutes and seconds
        :raises: ValueError
        """

        # "HH:MM:SS" has eight characters
        if len(label) != 8:
            raise ValueError("Label has invalid length (must be in HH-MM-SS format")

        tokens = label.split('-')

        # Ensure tokens is a list of three values ('HH', 'MM', 'SS')
        if len(tokens) != 3 or not all(map(lambda x: len(x) == 2, tokens)):
            raise ValueError("Label be in HH-MM-SS format")

        hours = int(tokens[0])
        minutes = int(tokens[1])
        seconds = int(tokens[2])

        if hours < 0 or hours > 23 or minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59:
            raise ValueError("Label must be in HH-MM-SS format")

        return hours, minutes, seconds
