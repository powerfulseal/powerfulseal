
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
from openstack import connection, config
from . import AbstractDriver
from ..node import Node, NodeState


def create_connection_from_config(name=None):
    """ Creates a new open stack connection """
    occ = config.OpenStackConfig()
    cloud = occ.get_one_cloud(name)
    return connection.from_config(cloud_config=cloud)

def get_all_ips(server):
    """
        Digs out all the IPs from the server.addresses field
        of an open stack server.
    """
    output = []
    addresses = server.addresses
    for addr_list in addresses.values():
        for addr in addr_list:
            for name, val in addr.items():
                if name == "addr":
                    output.append(val)
    return sorted(output)

# https://developer.openstack.org/sdks/python/openstacksdk/users/resources/compute/v2/server.html#openstack.compute.v2.server.Server
MAPPING_STATES_STATUS = {
    "ACTIVE": NodeState.UP,
    "STOPPED": NodeState.DOWN,
    "SHUTOFF": NodeState.DOWN,
}
def server_status_to_state(status):
    return MAPPING_STATES_STATUS.get(status.upper(), NodeState.UNKNOWN)

def create_node_from_server(server):
    """ Translate OpenStack server representation into a Node object.
        Same IP for private (ip) and public IPs (extIp)
    """
    return Node(
        id=server.id,
        ip=get_all_ips(server)[-1],
        extIp=get_all_ips(server)[-1],
        az=server.availability_zone,
        name=server.name,
        state=server_status_to_state(server.status),
    )


class OpenStackDriver(AbstractDriver):
    """
        Concrete implementation of the OpenStack cloud driver.
    """

    def __init__(self, cloud=None, conn=None, logger=None):
        self.logger = logger or makeLogger(__name__)
        self.conn = conn or create_connection_from_config(cloud)
        self.remote_servers = []

    def sync(self):
        """ Downloads a fresh set of nodes form the API.
        """
        self.logger.debug("Synchronizing remote nodes")
        self.remote_servers = list(self.conn.compute.servers())
        self.logger.info("Fetched %s remote servers" % len(self.remote_servers))

    def get_by_ip(self, ip):
        """ Retreive an instance of Node by its IP.
        """
        for server in self.remote_servers:
            addresses = get_all_ips(server)
            if not addresses:
                self.logger.warning("No addresses found: %s", server)
            else:
                for addr in addresses:
                    if addr == ip:
                        return create_node_from_server(server)
        return None

    def stop(self, node):
        """ Stop a Node.
        """
        self.conn.compute.stop_server(node.id)

    def start(self, node):
        """ Start a Node.
        """
        self.conn.compute.start_server(node.id)

    def delete(self, node):
        """ Delete a Node permanently.
        """
        self.conn.compute.delete_server(node.id)

