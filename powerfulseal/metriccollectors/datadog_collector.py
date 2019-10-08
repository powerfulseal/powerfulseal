from powerfulseal.metriccollectors.collector import AbstractCollector
from datadog import statsd

STATUS_SUCCESS = 'success'
STATUS_FAILURE = 'failure'

POD_KILLS_METRIC_NAME = 'powerfulseal.pod_kills_total'
POD_KILLS = ['status:', 'namespace:', 'name:']
NODE_STOPS_METRIC_NAME = 'powerfulseal.nodes_stopped_total'
NODE_STOPS = ['status:', 'id:', 'name:']
EXECUTE_FAILED_METRIC_NAME = 'powerfulseal.execute_failed_total'
EXECUTE_FAILURES = ['id:', 'name:']
FILTERED_TO_EMPTY_SET_METRIC_NAME = 'powerfulseal.empty_filter_total'
PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME = 'powerfulseal.probability_filter_not_passed_total'
MATCHED_TO_EMPTY_SET_METRIC_NAME = 'powerfulseal.empty_match_total'
MATCHED_TO_EMPTY_SET = ['source:']


def name_tags(names, tags):
    return [str(a) + b for a, b in zip(names, tags)]


class DatadogCollector(AbstractCollector):
    """
        Collects metrics to Datadog
    """

    def add_pod_killed_metric(self, pod):
        statsd.increment(POD_KILLS_METRIC_NAME, tags=name_tags(
            POD_KILLS, [STATUS_SUCCESS, pod.namespace, pod.name]))

    def add_pod_kill_failed_metric(self, pod):
        statsd.increment(POD_KILLS_METRIC_NAME, tags=name_tags(
            POD_KILLS, [STATUS_FAILURE, pod.namespace, pod.name]))

    def add_node_stopped_metric(self, node):
        statsd.increment(NODE_STOPS_METRIC_NAME, tags=name_tags(
            NODE_STOPS, [STATUS_SUCCESS, node.id, node.name]))

    def add_node_stop_failed_metric(self, node):
        statsd.increment(NODE_STOPS_METRIC_NAME, tags=name_tags(
            NODE_STOPS, [STATUS_FAILURE, node.id, node.name]))

    def add_execute_failed_metric(self, node):
        statsd.increment(EXECUTE_FAILED_METRIC_NAME, tags=name_tags(
            EXECUTE_FAILURES, [node.id, node.name]))

    def add_filtered_to_empty_set_metric(self):
        statsd.increment(FILTERED_TO_EMPTY_SET_METRIC_NAME)

    def add_probability_filter_passed_no_nodes_filter(self):
        statsd.increment(PROBABILITY_FILTER_NOT_PASSED_METRIC_NAME)

    def add_matched_to_empty_set_metric(self, source):
        statsd.increment(MATCHED_TO_EMPTY_SET_METRIC_NAME,
                         tags=name_tags(MATCHED_TO_EMPTY_SET, [source]))
