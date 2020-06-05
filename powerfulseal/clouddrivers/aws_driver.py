from powerfulseal import makeLogger
import boto3
from . import AbstractDriver
from ..node import Node, NodeState


def create_connection_from_config():
    """ Creates a new aws api connection """
    conn = boto3.resource('ec2')
    return conn

def get_all_ips(instance):
    """ Returns the public and private ip addresses of an AWS EC2 instances
    """
    output = []
    output.append(instance.private_ip_address)
    output.append(instance.public_ip_address)
    return output

#https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
MAPPING_STATES_STATUS = {
    "RUNNING": NodeState.UP,
    "STOPPED": NodeState.DOWN,
    "TERMINATED": NodeState.DOWN,
}

def server_status_to_state(status):
    return MAPPING_STATES_STATUS.get(status['Name'].upper(), NodeState.UNKNOWN)

def create_node_from_server(server):
    """ Translate AWS EC2 Instance representation into a Node object.
    """
    return Node(
        id=server.id,
        ip=server.private_ip_address,
        extIp=server.public_ip_address,
        az=server.placement['AvailabilityZone'],
        name="",
        state=server_status_to_state(server.state),
)

class AWSDriver(AbstractDriver):
    """
        Concrete implementation of the AWS cloud driver.
    """

    def __init__(self, cloud=None, conn=None, logger=None):
        self.logger = logger or makeLogger(__name__)
        self.conn = create_connection_from_config()
        self.instances = []

    def sync(self):
        """ Downloads a fresh set of nodes form the API.
        """
        self.logger.debug("Synchronizing remote nodes")
        self.remote_servers = self.conn.instances.all()
        self.amount_of_servers = list(self.conn.instances.all())
        self.logger.info("Fetched %s remote servers" % len(self.amount_of_servers))

    def get_by_ip(self, ip):
        """ Retrieve an instance of Node by its IP.
        """
        for server in self.remote_servers:
            addresses = get_all_ips(server)
            if not addresses:
                self.logger.warning("No ip addresses found: %s", server)
            else:
                for addr in addresses:
                    if addr == ip:
                        return create_node_from_server(server)
        return None

    def stop(self, node):
        """ Stop a Node.
        """
        self.conn.instances.filter(InstanceIds=(node.id.split())).stop()

    def start(self, node):
        """ Start a Node.
        """
        self.conn.instances.filter(InstanceIds=(node.id.split())).start()

    def delete(self, node):
        """ Delete a Node permanently.
        """
        self.conn.instances.filter(InstanceIds=(node.id.split())).terminate()
