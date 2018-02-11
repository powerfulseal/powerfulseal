import pytest
from mock import patch, MagicMock
from powerfulseal.clouddrivers import aws_driver
from powerfulseal.node import Node

IPS = ['198.168.1.1', '198.168.2.1']

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
def test_aws_driver(create_connection_from_config, ec2_instances):
    some = aws_driver.AWSDriver()
    some.remote_servers = ec2_instances
    nodes = some.get_by_ip(IPS[0])
    assert ec2_instances[0].id is nodes.id
    assert ec2_instances[0].placement['AvailabilityZone'] is nodes.az
    assert ec2_instances[0].private_ip_address == nodes.ip