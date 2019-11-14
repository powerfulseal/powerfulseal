import pytest
import os
from mock import patch, MagicMock
from powerfulseal.clouddrivers import gcp_driver
from powerfulseal.node import Node

PRIVATE_IPS = ['198.168.1.1', '198.168.2.1']
PUBLIC_IPS = ['31.31.31.31', '41.41.41.41']
INVALID_IP = '198.168.3.1'

GCLOUD_CONFIG = os.path.join(os.path.dirname(__file__), "mock_gcloud_config.json")


class Computeinstance():
    def __init__(
            self,
            id,
            private_ip_address,
            public_ip_address,
            zone,
            state,
            name):
        self.private_ip_address = private_ip_address
        self.id = id
        self.public_ip_address = public_ip_address
        self.placement = zone
        self.state = state
        self.name = name

    def show_as_dict(self):
        return {'name': self.name,
                'id': self.id,
                'zone': 'url/' + self.placement,
                'status': self.state,
                'networkInterfaces': [{'networkIP': self.private_ip_address,
                                       'accessConfigs': [{'natIP': self.public_ip_address}]}]}


@pytest.fixture
def compute_instances():
    return [
        Computeinstance(
            id="6285420104283695093",
            private_ip_address="198.168.1.1",
            zone="us-central1",
            public_ip_address="31.31.31.31",
            state="RUNNING",
            name="gke--cluster-1-pool-1-902c09f2-l5hf").show_as_dict(),
        Computeinstance(
            id="5611252125784513532",
            private_ip_address="198.168.2.1",
            zone="us-central2",
            public_ip_address="41.41.41.41",
            state="RUNNING",
            name="gke--cluster-1-pool-1-906c09e4-l9gh").show_as_dict()]


@patch('powerfulseal.clouddrivers.gcp_driver.create_connection_from_config')
def test_get_by_ip_private_ip_nodes(
        create_connection_from_config,
        compute_instances):
    driver = gcp_driver.GCPDriver(config=GCLOUD_CONFIG)
    driver.remote_servers = compute_instances
    node_index = 0
    nodes = driver.get_by_ip(PRIVATE_IPS[node_index])
    assert compute_instances[node_index]['id'] is nodes.id
    assert compute_instances[node_index]['zone'] == 'url/' + nodes.az
    assert compute_instances[node_index]['networkInterfaces'][0]['networkIP'] == nodes.ip


@patch('powerfulseal.clouddrivers.gcp_driver.create_connection_from_config')
def test_get_by_ip_public_ip_nodes(
        create_connection_from_config,
        compute_instances):
    driver = gcp_driver.GCPDriver(config=GCLOUD_CONFIG)
    driver.remote_servers = compute_instances
    node_index = 1
    nodes = driver.get_by_ip(PUBLIC_IPS[node_index])
    assert compute_instances[node_index]['id'] is nodes.id
    assert compute_instances[node_index]['zone'] == 'url/' + nodes.az
    assert compute_instances[node_index]['networkInterfaces'][0]['accessConfigs'][0]['natIP'] == nodes.extIp


@patch('powerfulseal.clouddrivers.gcp_driver.create_connection_from_config')
def test_get_by_ip_no_nodes(create_connection_from_config, compute_instances):
    driver = gcp_driver.GCPDriver(config=GCLOUD_CONFIG)
    driver.remote_servers = compute_instances
    nodes = driver.get_by_ip(INVALID_IP)
    assert nodes is None
