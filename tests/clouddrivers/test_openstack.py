from mock import MagicMock
import pytest

from powerfulseal.clouddrivers.open_stack_driver import (
    get_all_ips,
    create_node_from_server,
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
