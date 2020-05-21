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

from abc import ABC, abstractmethod

# Used to identify the source of metrics for actions which can be performed on
# both pods and nodes
POD_SOURCE = 'pods'
NODE_SOURCE = 'nodes'


class AbstractCollector(ABC):
    """
        Metric collectors record events which are useful to users. The storage
        of these metrics is handled by the the collectors which extend this
        abstract class.
    """

    @abstractmethod
    def add_pod_killed_metric(self, pod):
        pass  # pragma: nocover

    @abstractmethod
    def add_pod_kill_failed_metric(self, pod):
        pass  # pragma: nocover

    @abstractmethod
    def add_node_stopped_metric(self, node):
        pass  # pragma: nocover

    @abstractmethod
    def add_node_stop_failed_metric(self, node):
        pass  # pragma: nocover

    @abstractmethod
    def add_execute_failed_metric(self, node):
        pass  # pragma: nocover

    @abstractmethod
    def add_filtered_to_empty_set_metric(self):
        pass  # pragma: nocover

    @abstractmethod
    def add_probability_filter_passed_no_nodes_filter(self):
        pass  # pragma: nocover

    @abstractmethod
    def add_matched_to_empty_set_metric(self, source):
        pass  # pragma: nocover
