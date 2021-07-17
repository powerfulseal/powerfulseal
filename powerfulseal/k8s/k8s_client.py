
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
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException

K8S_CRD_GROUP = "powerfulseal.io"
K8S_CRD_VERSION = "v1"
K8S_CRD_PLURAL = "scenarios"

class K8sClient():
    """ Higher level Kubernetes client.
    """

    def __init__(self, kube_config=None, logger=None):
        if kube_config:
            kubernetes.config.load_kube_config(config_file=kube_config)
        else:
            kubernetes.config.load_incluster_config()

        proxy_url = os.getenv('HTTP_PROXY', None)
        if proxy_url:
            kubernetes.client.Configuration._default.proxy = proxy_url

        ca_cert_file = os.getenv('SSL_CERT_FILE', None)
        if ca_cert_file:    
            kubernetes.client.Configuration._default.ssl_ca_cert = ca_cert_file

        self.kube_config = kube_config
        self.client_corev1api = kubernetes.client.CoreV1Api()
        self.client_appsv1api = kubernetes.client.AppsV1Api()
        self.client_extensionsApi = kubernetes.client.ApiextensionsV1beta1Api()
        self.client_customObjectsApi = kubernetes.client.CustomObjectsApi()

        self.logger = logger or makeLogger(__name__)
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
        try:
            selector = self.selector_or_labels(labels, selector)
            return self.client_appsv1api.list_namespaced_deployment(
                namespace=namespace,
                label_selector=selector,
            ).items
        except ApiException as e:
            self.logger.exception(e)
            raise

    def get_deployment(self, namespace, name):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#read_namespaced_deployment
        """
        try:
            return self.client_appsv1api.read_namespaced_deployment(
                namespace=namespace,
                name=name,
            )
        except ApiException as e:
            self.logger.exception(e)
            raise

    def create_deployment(self, namespace, body):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#create_namespaced_deployment
        """
        try:
            return self.client_appsv1api.create_namespaced_deployment(
                namespace=namespace,
                body=body,
            )
        except ApiException as e:
            self.logger.exception(e)
            raise


    def delete_deployment(self, namespace, name):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#delete_namespaced_deployment
        """
        try:
            return self.client_appsv1api.delete_namespaced_deployment(
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
        try:
            selector = self.selector_or_labels(labels, selector)
            if deployment_name:
                deployment = self.get_deployment(namespace, deployment_name)
                selector = self.dict_to_selector(deployment.spec.selector.match_labels)
            return self.client_corev1api.list_namespaced_pod(
                namespace=namespace,
                label_selector=selector,
            ).items
        except ApiException as e:
            self.logger.exception(e)
            raise

    def delete_pods(self, pods):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            CoreV1Api.md#delete_namespaced_pod
            Delete all pods synchronously
        """
        for pod in pods:
            try:
                self.client_corev1api.delete_namespaced_pod(
                    name=pod.name,
                    namespace=pod.namespace,
                    grace_period_seconds=0
                )
            except ApiException as e:
                self.logger.exception(e)
                return False
        return True

    def get_service(self, namespace, name):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            /CoreV1Api.md#read_namespaced_service
        """
        try:
            return self.client_corev1api.read_namespaced_service(
                namespace=namespace,
                name=name,
            )
        except ApiException as e:
            self.logger.exception(e)
            raise

    def get_scenarios(self, namespaces="", labels=None, selector=None):
        """
            https://github.com/kubernetes-incubator/client-python/blob/master/kubernetes/docs/
            ExtensionsV1beta1Api.md#list_namespaced_deployment
        """
        try:
            crds = self.client_extensionsApi.list_custom_resource_definition().to_dict()['items']
            crd = None
            for x in crds:
                if x['spec']['names']['plural'].lower() == K8S_CRD_PLURAL and \
                        x['spec']['group'].lower() == K8S_CRD_GROUP:
                    crd = x
            if crd == None:
                return []

            scenarios = self.client_customObjectsApi.list_namespaced_custom_object(
                K8S_CRD_GROUP,
                K8S_CRD_VERSION,
                namespaces,
                K8S_CRD_PLURAL)
            out = []
            for scenario in scenarios['items']:
                out.append(scenario['spec'])
            self.logger.debug("Read %d scenarios from CRDS", len(out))
            return out
        except ApiException as e:
            if e.status == 403:
                self.logger.info("No permission to list powerfulseal CRDs. Ignoring.")
                return []
            self.logger.exception(e)
            raise
