import pytest
from mock import patch, MagicMock
from powerfulseal.clouddrivers import aws_driver
from powerfulseal.node import Node

PRIVATE_IPS = ['198.168.1.1', '198.168.2.1']
PUBLIC_IPS = ['31.31.31.31', '41.41.41.41']
INVALID_IP = '198.168.3.1'

class EC2instance():
    def __init__(self, id, private_ip_address, public_ip_address, zone, state):
        self.private_ip_address = private_ip_address
        self.id = id
        self.public_ip_address = public_ip_address
        self.placement = {}
        self.placement = {'AvailabilityZone': zone}
        self.state = {'Name': state}

@pytest.fixture
def ec2_instances():
    return [
        EC2instance(id="i-123456789", private_ip_address="198.168.1.1", zone="us-east-1a", public_ip_address="31.31.31.31", state="Running"),
        EC2instance(id="i-987654321", private_ip_address="198.168.2.1", zone="us-east-1b", public_ip_address="41.41.41.41", state="Running"),
]

@patch('powerfulseal.clouddrivers.aws_driver.create_connection_from_config')
def test_get_by_ip_private_ip_nodes(create_connection_from_config, ec2_instances):
    driver = aws_driver.AWSDriver()
    driver.remote_servers = ec2_instances
    node_index = 0
    nodes = driver.get_by_ip(PRIVATE_IPS[node_index])
    assert ec2_instances[node_index].id is nodes.id
    assert ec2_instances[node_index].placement['AvailabilityZone'] is nodes.az
    assert ec2_instances[node_index].private_ip_address == nodes.ip

@patch('powerfulseal.clouddrivers.aws_driver.create_connection_from_config')
def test_get_by_ip_public_ip_nodes(create_connection_from_config, ec2_instances):
    driver = aws_driver.AWSDriver()
    driver.remote_servers = ec2_instances
    node_index = 1
    nodes = driver.get_by_ip(PUBLIC_IPS[node_index])
    assert ec2_instances[node_index].id is nodes.id
    assert ec2_instances[node_index].placement['AvailabilityZone'] is nodes.az
    assert ec2_instances[node_index].public_ip_address == nodes.extIp

@patch('powerfulseal.clouddrivers.aws_driver.create_connection_from_config')
def test_get_by_ip_no_nodes(create_connection_from_config, ec2_instances):
    driver = aws_driver.AWSDriver()
    driver.remote_servers = ec2_instances
    nodes = driver.get_by_ip(INVALID_IP)
    assert nodes is None
