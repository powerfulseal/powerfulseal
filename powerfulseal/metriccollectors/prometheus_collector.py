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


from prometheus_client import Counter

from powerfulseal.metriccollectors import AbstractCollector
from powerfulseal.metriccollectors.collector import NODE_SOURCE, POD_SOURCE

STATUS_SUCCESS = 'success'
STATUS_FAILURE = 'failure'

# Define Prometheus metrics to be stored in the default registry
POD_KILLS_METRIC_NAME = 'seal_pod_kills_total'
POD_KILLS = Counter(POD_KILLS_METRIC_NAME,
                    'Number of pods killed (including failures)',
                    ['status', 'namespace', 'name'])

NODE_STOPS_METRIC_NAME = 'seal_nodes_stopped_total'
NODE_STOPS = Counter(NODE_STOPS_METRIC_NAME,
                     'Number of nodes stopped (including failures)',
                     ['status', 'id', 'name'])

EXECUTE_FAILED_METRIC_NAME = 'seal_execute_failed_total'
EXECUTE_FAILURES = Counter(EXECUTE_FAILED_METRIC_NAME,
                           'Increasing counter for command execution failures',
                           ['id', 'name'])

FILTERED_TO_EMPTY_SET_METRIC_NAME = 'seal_empty_filter_total'
FILTERED_TO_EMPTY_SET = Counter(FILTERED_TO_EMPTY_SET_METRIC_NAME,
                                'Increasing counter for cases where filtering '
                                'returns an empty result')

PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME = 'seal_probability_filter_not_passed_total'
PROBABILITY_FILTER_NOT_PASSED = Counter(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME,
                                        'Increasing counter for cases where the'
                                        ' probability filter does not pass any '
                                        'nodes')

MATCHED_TO_EMPTY_SET_METRIC_NAME = 'seal_empty_match_total'
MATCHED_TO_EMPTY_SET = Counter(MATCHED_TO_EMPTY_SET_METRIC_NAME,
                               'Increasing counter for cases where matching '
                               'returns an empty result',
                               ['source'])

SCENARIO_RUNS_METRIC_NAME = 'seal_scenario_runs_total'
SCENARIO_RUNS_TOTAL = Counter(SCENARIO_RUNS_METRIC_NAME,
                           'Counter of runs of scenarios (both success and failure)',
                           ['name', 'result'])


class PrometheusCollector(AbstractCollector):
    def __init__(self):
        # Export 0 for time series metrics which have labels which can have default
        # values filled to avoid missing metrics. The Prometheus Python library
        # already exports 0 for metrics which do not have any labels.
        MATCHED_TO_EMPTY_SET.labels(NODE_SOURCE).inc(0)
        MATCHED_TO_EMPTY_SET.labels(POD_SOURCE).inc(0)

    def add_pod_killed_metric(self, pod):
        POD_KILLS.labels(STATUS_SUCCESS, pod.namespace, pod.name).inc()

    def add_pod_kill_failed_metric(self, pod):
        POD_KILLS.labels(STATUS_FAILURE, pod.namespace, pod.name).inc()

    def add_node_stopped_metric(self, node):
        NODE_STOPS.labels(STATUS_SUCCESS, node.id, node.name).inc()

    def add_node_stop_failed_metric(self, node):
        NODE_STOPS.labels(STATUS_FAILURE, node.id, node.name).inc()

    def add_execute_failed_metric(self, node):
        EXECUTE_FAILURES.labels(node.id, node.name).inc()

    def add_filtered_to_empty_set_metric(self):
        FILTERED_TO_EMPTY_SET.inc()

    def add_probability_filter_passed_no_nodes_filter(self):
        PROBABILITY_FILTER_NOT_PASSED.inc()

    def add_matched_to_empty_set_metric(self, source):
        MATCHED_TO_EMPTY_SET.labels(source).inc()

    def add_scenario_counter_metric(self, name, result):
        res = "success" if result else "fail"
        SCENARIO_RUNS_TOTAL.labels(name, res).inc()
