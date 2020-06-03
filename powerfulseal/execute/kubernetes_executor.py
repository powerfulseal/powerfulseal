
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

from powerfulseal import makeLogger
import spur

from .abstract_executor import AbstractExecutor


class KubernetesExecutor(AbstractExecutor):
    """ Executes things by talking to Kubernetes API
    """

    def __init__(self, k8s_client, logger=None):
        self.k8s_client = k8s_client
        self.logger = logger or makeLogger(__name__)

    def kill_pod(self, pod, inventory, signal=None):
        return self.k8s_client.delete_pods([pod])

    def execute(self, *args, **kwargs):
        """ Noop for backwards compatibility"""
        self.logger.error("NOOP: can't execute arbitrary SSH commands in Kubernetes mode")
        return {}
