from mock import patch, MagicMock
import pytest

from powerfulseal.clouddrivers.open_stack_driver import (
    get_all_ips,
    create_node_from_server,
    create_connection_from_config,
    OpenStackDriver,
)
from powerfulseal.node import NodeState


@pytest.fixture
def example_servers():
    server1 = MagicMock()
    server1.addresses = dict(
        group1=[dict(addr="1.2.3.4")],
        group2=[dict(addr="11.22.33.44")],
        group_no_addr=[dict()],
        empty_group=[],
    )
    server1.id = "some_id"
    server1.availability_zone = "DC1"
    server1.name = "random server"
    server1.status = "ACTIVE"
    return [server1]

@pytest.fixture
def driver():
    mock_connection = MagicMock()
    return OpenStackDriver(conn=mock_connection)

@pytest.fixture
def example_node():
    node = MagicMock()
    node.id = "some_id"
    return node


def test_get_all_ips(example_servers):
    server = example_servers[0]
    res = get_all_ips(server)
    assert res == ["1.2.3.4", "11.22.33.44"]

def test_create_node_from_server(example_servers):
    server = example_servers[0]
    node = create_node_from_server(server)
    assert node.id == server.id
    assert node.ip == server.addresses["group2"][0]["addr"]
    assert node.az == server.availability_zone
    assert node.name == server.name
    assert node.state == NodeState.UP

def test_sync(driver):
    driver.sync()
    assert driver.conn.compute.servers.called

@pytest.mark.parametrize("method, compute_method", [
    ("stop", "stop_server"),
    ("start", "start_server"),
    ("delete", "delete_server"),
])
def test_cloud_methods(driver, example_node, method, compute_method):
    getattr(driver, method)(example_node)
    assert getattr(driver.conn.compute, compute_method).called

def test_get_by_ip(driver, example_servers):
    driver.remote_servers = example_servers
    server = example_servers[0]
    node = driver.get_by_ip("1.2.3.4")
    assert node.id == server.id
    assert node.ip == server.addresses["group2"][0]["addr"]
    assert node.az == server.availability_zone
    assert node.name == server.name
    assert node.state == NodeState.UP

def test_get_by_ip_empty(driver):
    driver.remote_servers = [MagicMock()]
    node = driver.get_by_ip("1.2.3.4")
    assert node is None

@patch('powerfulseal.clouddrivers.open_stack_driver.connection')
@patch('powerfulseal.clouddrivers.open_stack_driver.config')
def test_create_connection_from_config(config, connection):
    cloud_mock = MagicMock()
    occ_mock = MagicMock()
    occ_mock.get_one_cloud = MagicMock(return_value=cloud_mock)
    config.OpenStackConfig = MagicMock(return_value=occ_mock)

    # make the actual call
    name = "Boaty McBoatface"
    create_connection_from_config(name)

    assert config.OpenStackConfig.called
    assert occ_mock.get_one_cloud.called
    assert occ_mock.get_one_cloud.call_args[0] == (name,)
    assert connection.from_config.called

