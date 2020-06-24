
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

import requests
import time

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

    def get_headers(self, schema):
        headers = dict()
        for header in schema.get("headers",[]):
            headers[header["name"]] = header["value"]
        return headers

    def make_call(self, url, method, body, headers, timeout, code, proxy, verify):
        self.logger.info(
            "Making a call: %s, %s, %r, %d, %d, %s, %s, %s",
            url, method, headers, timeout, code, body, proxy, verify
        )
        try:
            resp = requests.request(
                method.upper(),
                url,
                headers=headers,
                timeout=timeout/1000,
                data=body.encode("utf-8"),
                proxies=dict(
                    http=proxy or "",
                    https=proxy or "",
                ),
                verify=verify,
            )
            resp.raise_for_status()
            self.logger.info("Response: %s", resp.text)
            return True
        except:
            self.logger.exception("Exception while calling %s", url)
        return False

    def execute(self):
        count = self.schema.get("count", 1)
        retries = self.schema.get("retries", 1)
        delay = self.schema.get("delay", 100)

        url = self.get_url(self.schema)
        headers = self.get_headers(self.schema)
        method = self.schema.get("method", "get")
        body = self.schema.get("body", "")
        timeout = self.schema.get("timeout", 1000)
        code = self.schema.get("code", 200)
        proxy = self.schema.get("proxy", "")
        insecure = self.schema.get("insecure", False)

        for _ in range(count):
            for retry in range(retries):
                success = self.make_call(
                    url=url,
                    method=method,
                    body=body,
                    headers=headers,
                    timeout=timeout,
                    code=code,
                    proxy=proxy,
                    verify=not insecure
                )
                if not success:
                    # if we've reached the limit, the answer is no
                    if retry == retries - 1:
                        self.logger.error("No more retries allowed. Failing step")
                        return False
                    self.logger.warning("Error calling. Sleeping %s and retrying", delay)
                    # otherwise just wait a little
                    time.sleep(delay/1000)
                else:
                    break

        return True
