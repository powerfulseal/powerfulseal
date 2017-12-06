
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
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException


class K8sClient():
    """ Higher level Kubernetes client.
    """

    def __init__(self, kube_config=None, logger=None):
        if kube_config:
            kubernetes.config.load_kube_config(config_file=kube_config)
        self.client_corev1api = kubernetes.client.CoreV1Api()
        self.client_extensionsv1beta1api = kubernetes.client.ExtensionsV1beta1Api()

        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("Initializing with config: %s", kube_config)

    def make_selector(self, key, value):
        """ Helper to support the name -> !value notation
        """
        if isinstance(value, str) and value.startswith("!"):
            op = "!="
            value = value[1:]
        else:
            op = "="
        return "{key}{op}{value}".format(key=key, op=op, value=value)

    def dict_to_selector(self, payload):
        """ Translates a dict into kubernetes label format
            https://kubernetes.io/docs/user-guide/labels/
        """
        if payload:
            return ",".join(self.make_selector(*item) for item in payload.items())

    def get_nodes_groups(self):
        """ Returns an inventory of nodes which form the Kubernetes cluster.
            Returns a dict of group name -> list of nodes.
        """
        nodes = self.list_nodes()
        groups = dict()
        for node in nodes:
            name = node.metadata.name
            labels = node.metadata.labels
            addresses = node.status.addresses
            ips = []
            if addresses:
                ips = [addr.address for addr in addresses]
            for label, value in labels.items():
                group = groups.get(value, [])
                for ip in ips:
                    if ip not in group:
                        group.append(ip)
                groups[value] = group
        return groups

    def list_nodes(self):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            CoreV1Api.md##list_node
        """
        try:
            resp = self.client_corev1api.list_node()
            return resp.items
        except ApiException as e:
            self.logger.exception(e)
            raise

    def list_namespaces(self):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            CoreV1Api.md#list_namespace
        """
        try:
            resp = self.client_corev1api.list_namespace()
            return resp.items
        except ApiException as e:
            self.logger.exception(e)
            raise

    def selector_or_labels(self, labels, selector):
        """ Helper to select labels over selector.
        """
        if selector is None:
            selector = ""
        if labels is not None:
            selector = self.dict_to_selector(labels)
        return selector

    def list_deployments(self, namespace, labels=None, selector=None):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#list_namespaced_deployment
        """
        selector = self.selector_or_labels(labels, selector)
        return self.client_extensionsv1beta1api.list_namespaced_deployment(
            namespace=namespace,
            label_selector=selector,
        ).items

    def get_deployment(self, namespace, name):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#read_namespaced_deployment
        """
        try:
            return self.client_extensionsv1beta1api.read_namespaced_deployment(
                namespace=namespace,
                name=name,
            )
        except ApiException as e:
            self.logger.exception(e)
            raise

    def list_pods(self, namespace, labels=None, deployment_name=None, selector=None):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            CoreV1Api.md#list_namespaced_pod
            If deployment_name is provided, it will ignore selector, and use the deployment's
        """
        selector = self.selector_or_labels(labels, selector)
        if deployment_name:
            deployment = self.get_deployment(namespace, deployment_name)
            selector = self.dict_to_selector(deployment.spec.selector.match_labels)
        return self.client_corev1api.list_namespaced_pod(
            namespace=namespace,
            label_selector=selector,
        ).items
