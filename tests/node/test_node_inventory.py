
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


import pytest
from mock import MagicMock

from powerfulseal.node import Node, NodeInventory



@pytest.fixture
def nodes():
    return [
        Node(id="id1", ip="198.168.1.1", extIp="10.22.66.1", az="AZ1", no=1, name="node1"),
        Node(id="id2", ip="198.168.2.1", extIp="10.22.66.2", az="AZ2", no=2, name="node2"),
        Node(id="id3", ip="198.168.3.1", extIp="10.22.66.3", az="AZ2", no=3, name="node3"),
    ]

@pytest.fixture
def mock_driver(nodes):
    mock = MagicMock()
    mock.nodes = nodes
    def get_by_ip(ip):
        for node in mock.nodes:
            if (node.ip == ip) or (node.extIp == ip):
                return node
    mock.get_by_ip = get_by_ip
    return mock


def test_sync(nodes, mock_driver):
    inventory = NodeInventory(
        driver=mock_driver,
        restrict_to_groups={
            "TEST1": ["198.168.1.1"],
            "TEST2": ["198.168.1.1", "198.168.2.1"],
        }
    )
    inventory.sync()
    assert inventory.groups == {
        "TEST1": nodes[0:1],
        "TEST2": nodes[0:2]
    }
    assert inventory.get_azs() == ["AZ1", "AZ2"]

@pytest.mark.parametrize("query, expected_indices", [
    (None, [0, 1]),
    ("all", [0, 1]),
    ("id1,id2", [0, 1]),
    ("id1", [0]),
    ("id2", [1]),
    ("198.168.1.1", [0]),
    ("10.22.66.2", [1]),
    ("10.22.66.4", []),
    ("AZ2", [1]),
    ("2", [1]),
    ("node2", [1]),
    ("TEST2", [0, 1]),
    ("up", []),
    ("unknown", [0, 1]),
    ("something-weird", []),
])
def test_find(nodes, mock_driver, query, expected_indices):
    inventory = NodeInventory(
        driver=mock_driver,
        restrict_to_groups={
            "TEST1": ["198.168.1.1"],
            "TEST2": ["198.168.1.1", "198.168.2.1"],
        }
    )
    inventory.sync()
    assert list(inventory.find_nodes(query)) == [nodes[x] for x in expected_indices]


@pytest.mark.parametrize("ip, should_find, index", [
    ("198.168.2.1", True, 1),
    ("doesn't exist", False, None),
])
def test_get_by_ip(nodes, mock_driver, ip, should_find, index):
    inventory = NodeInventory(
        driver=mock_driver,
        restrict_to_groups={
            "TEST1": ["198.168.1.1"],
            "TEST2": ["198.168.1.1", "198.168.2.1"],
        }
    )
    inventory.sync()
    if should_find:
        assert inventory.get_node_by_ip(ip) is nodes[index]
    else:
        assert inventory.get_node_by_ip(ip) == None

def test_groups(mock_driver):
    inventory = NodeInventory(
        driver=mock_driver,
        restrict_to_groups={
            "TEST1": ["198.168.1.1"],
            "TEST2": ["198.168.1.1", "198.168.2.1"],
        }
    )
    inventory.sync()
    assert inventory.get_groups() == ["TEST1", "TEST2"]

