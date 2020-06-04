
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

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_abstract import ActionAbstract


class ActionProbeHTTP(ActionAbstract):

    def __init__(self, name, schema, k8s_inventory, logger=None, metric_collector=None):
        self.name = name
        self.schema = schema
        self.k8s_inventory = k8s_inventory
        self.logger = logger or makeLogger(__name__, name)
        self.metric_collector = metric_collector or StdoutCollector()


    def get_url(self, schema):
        target = schema.get("target",{})
        endpoint = schema.get("endpoint", "").lstrip("/")
        if "service" in target:
            service_name = target.get("service").get("name")
            service_namespace = target.get("service").get("namespace")
            service_port = target.get("service").get("port", 80)
            service_protocol = target.get("service").get("protocol", "http")
            self.logger.debug(
                "Matching service %s (%s), port %d, proto %s, endpoint %s",
                service_name, service_namespace, service_port, service_protocol,
                endpoint
            )
            service = self.k8s_inventory.get_service(
                name=service_name,
                namespace=service_namespace,
            )
            if not service:
                self.logger.error("Service not found")
                return None
            url = "{protocol}://{ip}:{port}/{endpoint}".format(
                protocol=service_protocol,
                ip=service.spec.cluster_ip,
                port=service_port,
                endpoint=endpoint
            )
            self.logger.debug("Url: %s", url)
            return url
        url = "{url}/{endpoint}".format(
            url=target.get("url").rstrip("/"),
            endpoint=endpoint,
        )
        self.logger.debug("Using provided url: %s", url)
        return url

    def execute(self):
        url = self.get_url(self.schema)
        self.logger.info("Using url: %s", url)
        return True
