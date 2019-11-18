
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


import logging
from datetime import datetime
from .pod import Pod


def get_status(status):
    # try to find the error reasons, if any
    try:
        reasons = [x.state.waiting.reason for x in status.container_statuses]
        return ','.join(reasons)
    except:
        return status.phase

class K8sInventory():
    """ Kubernetes inventory - deal with namespaces, deployments and pods.
        Also manages cache.
    """

    def __init__(self, k8s_client, delete_pods=False, logger=None):
        self.k8s_client = k8s_client
        self._cache_namespaces = []
        self._cache_last = None
        self.delete_pods = delete_pods
        self.logger = logger or logging.getLogger(__name__)
        self.last_pods = []

    def is_fresh(self, when):
        """ Helper to invalidate the cache.
        """
        delta = datetime.now() - when
        if delta.seconds > 10:
            return False
        return True

    def preprocess_namespace(self, namespace):
        # Check if namespace is None instead of using "or" as Kubernetes treats
        # an empty string as the */all wildcard
        if namespace is None:
            namespace = "default"
        if namespace == "*":
            namespace = ""
        return namespace

    def find_namespaces(self):
        """ Returns all namespaces.
        """
        if self._cache_last is not None and self.is_fresh(self._cache_last):
            self.logger.info("Using cached namespaces")
            return self._cache_namespaces
        self.logger.info("Reading kubernetes namespaces")
        namespaces = [
            item.metadata.name for item in self.k8s_client.list_namespaces()
        ]
        self._cache_namespaces = namespaces
        self._cache_last = datetime.now()
        return namespaces

    def find_deployments(self, namespace=None, labels=None):
        """ Find deployments for a namespace (default to "default" namespace).
        """
        namespace = self.preprocess_namespace(namespace)
        return [
            item.metadata.name
            for item in self.k8s_client.list_deployments(
                namespace=namespace,
                labels=labels,
            )
        ]

    def find_pods(self, namespace, selector=None, deployment_name=None):
        """ Find pods in a namespace, for a deployment or selector.
        """
        namespace = self.preprocess_namespace(namespace)
        pods = self.k8s_client.list_pods(
            namespace=namespace,
            selector=selector,
            deployment_name=deployment_name,
        )
        pod_objects = []
        if pods is not None:
            for i, item in enumerate(pods):
                        container_ids = []
                        restart_count = []
                        if item.status.container_statuses:
                            for status in item.status.container_statuses:
                                container_ids.append(status.container_id)
                                restart_count.append(status.restart_count)
                        
                        pod_objects.append(Pod(
                            num=i,
                            name=item.metadata.name,
                            namespace=item.metadata.namespace,
                            uid=item.metadata.uid,
                            host_ip=item.status.host_ip,
                            ip=item.status.pod_ip,
                            container_ids=container_ids,
                            restart_count=sum(restart_count),
                            state=get_status(item.status),
                            labels=item.metadata.labels,
                            meta=item,
                        ))
        self.last_pods = pod_objects
        return pod_objects

    def get_all_pods(self):
        """
        Retrieves all pods for all namespaces
        """
        return self.find_pods("")
