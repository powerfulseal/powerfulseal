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

# Define Prometheus metrics to be stored in the default registry
STATUS_SUCCESS = 'success'
STATUS_FAILURE = 'failure'

POD_KILLS_METRIC_NAME = 'seal_pod_kills_total'
POD_KILLS = Counter(POD_KILLS_METRIC_NAME,
                    'Number of pods killed (including failures)',
                    ['status'])

NODE_STOPS_METRIC_NAME = 'seal_nodes_stopped_total'
NODE_STOPS = Counter(NODE_STOPS_METRIC_NAME,
                     'Number of nodes stopped (including failures)',
                     ['status'])

EXECUTE_FAILED_METRIC_NAME = 'seal_execute_failed_total'
EXECUTE_FAILURES = Counter(EXECUTE_FAILED_METRIC_NAME,
                           'Increasing counter for command execution failures')

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
                               'returns an empty result')


class PrometheusCollector(AbstractCollector):
    def add_pod_killed_metric(self, node):
        POD_KILLS.labels(STATUS_SUCCESS).inc()

    def add_pod_kill_failed_metric(self, node):
        POD_KILLS.labels(STATUS_FAILURE).inc()

    def add_node_stopped_metric(self, node):
        NODE_STOPS.labels(STATUS_SUCCESS).inc()

    def add_node_stop_failed_metric(self, node):
        NODE_STOPS.labels(STATUS_FAILURE).inc()

    def add_execute_failed_metric(self):
        EXECUTE_FAILURES.inc()

    def add_filtered_to_empty_set_metric(self):
        FILTERED_TO_EMPTY_SET.inc()

    def add_probability_filter_passed_no_nodes_filter(self):
        PROBABILITY_FILTER_NOT_PASSED.inc()

    def add_matched_to_empty_set_metric(self):
        MATCHED_TO_EMPTY_SET.inc()
