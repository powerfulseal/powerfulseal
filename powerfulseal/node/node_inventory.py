
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
import ipaddress
from .node import Node, NodeState

class NodeInventory():

    def __init__(self, driver, restrict_to_groups=None, filters=None, logger=None):
        self.logger = logger or makeLogger(__name__)
        self.driver = driver
        self.filters = filters or []
        self.local_ips = restrict_to_groups or {}
        self.groups = {}
        self.nodes_by_id = {}
        self.nodes_by_ip = {}
        self.azs = set()

    def get_all_nodes(self, sort_key="no"):
        nodes = self.nodes_by_id.values()
        return sorted(nodes, key=lambda x: getattr(x, sort_key))

    def get_node_by_ip(self, ip):
        return self.nodes_by_ip.get(ip, None)

    def find_nodes(self, query=None):
        """
            Universal node finder.
        """

        # all the queries and 'all' keyword
        if not query or query == 'all':
            for node in self.get_all_nodes():
                yield node
            return

        # support comma-separated queries
        if query and "," in query:
            for element in query.split(","):
                for node in self.find_nodes(element):
                    yield node
            return

        # match groups
        if query in self.groups.keys():
            for node in self.groups[query]:
                yield node
            return

        # match AZ
        if query in self.azs:
            for node in self.get_all_nodes():
                if node.az == query:
                    yield node
            return

        # match IP or ID or no or name
        for node in self.get_all_nodes():
            if (
                node.id == query
                or node.ip == query
                or node.extIp == query
                or str(node.no) == str(query)
                or node.name == query
            ):
                yield node
                return

        # match by state
        try:
            state = NodeState[query.upper()]
        except KeyError:
            pass
        else:
            for node in self.get_all_nodes():
                if node.state == state:
                    yield node

    def sync(self, driver=None):
        """
            Update the nodes based on the values returned from the driver
        """
        self.logger.debug("Sync Nodes")
        driver = driver or self.driver
        driver.sync()
        counter = 0
        self.groups = {}
        self.nodes_by_id = {}
        self.nodes_by_ip = {}
        self.azs = set()

        for group, ips in sorted(self.local_ips.items()):
            self.groups[group] = []

            # different groups can have the same IPs,
            # so we need to match to the same nodes
            for ip in ips:
                self.logger.debug("IP processing: %s", ip)
                # see if we have a matching node in the cached list of nodes
                node = self.nodes_by_ip.get(ip)
                if node is None:
                    # node is not in cached list (or the list is empty), check the clouddriver
                    node = driver.get_by_ip(ip)
                if node is None: #pragma: no cover
                    # apart from IPs, we will also get hostnames here
                    # for those, debug, otherwise info
                    try:
                        # validate that this is an IP or not
                        ipaddress.ip_address(ip)
                        self.logger.debug("Couldn't match IP to any cloud node: %s", ip)
                    except:
                        self.logger.debug("Couldn't match to any cloud node: %s", ip)
                    continue

                self.nodes_by_id[node.id] = node
                self.nodes_by_ip[ip] = node
                self.groups[group].append(node)
                node.groups.append(group)
                self.azs.add(node.az)

                self.logger.debug("Node added: %s", node)

                # just for easier identification, give them numbers
                node.no = counter
                counter += 1

    def get_azs(self):
        return sorted(list(self.azs))

    def get_groups(self):
        return sorted(list(self.groups.keys()))
