
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


import abc


class AbstractCollector(metaclass=abc.ABCMeta):
    """
        Metric collectors record events which are useful to users. The storage
        of these metrics is handled by the the collectors which extend this
        abstract class.
    """

    @abc.abstractmethod
    def add_pod_killed_metric(self, node):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_pod_kill_failed_metric(self, node):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_node_stopped_metric(self, node):
        pass  #pragma: nocover

    @abc.abstractmethod
    def add_node_stop_failed_metric(self, node):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_action_failed_metric(self):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_filtered_to_empty_set_metric(self):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_filtered_to_insufficient_random_sample_metric(self, sample_size, criterion):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_filtering_passed_all_nodes_metric(self):
        pass #pragma: nocover

    @abc.abstractmethod
    def add_matched_to_empty_set_metric(self):
        pass #pragma: nocover
