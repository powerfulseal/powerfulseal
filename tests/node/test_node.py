
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
from powerfulseal.node import Node, NodeState

EXAMPLE_NODE_ARGS = dict(
    id="someid",
    name="random_node",
    ip="198.198.1.1",
    extIp="31.41.51.61",
    az="az1",
    groups=["group1","group2"],
    state=NodeState.UP,
)

@pytest.fixture
def node():
    return Node(**EXAMPLE_NODE_ARGS)


def test_node_passthrough(node):
    for key, val in EXAMPLE_NODE_ARGS.items():
        assert key in node.__dict__
        assert val == node.__dict__.get(key)

def test_node_str(node):
    rep = str(node)
    for key, val in EXAMPLE_NODE_ARGS.items():
        assert key in rep
        assert str(val) in rep

def test_node_repr(node):
    rep = repr(node)
    for key, val in EXAMPLE_NODE_ARGS.items():
        assert key in rep
        assert str(val) in rep

def test_node_state(node):
    node.state = NodeState.UP
    assert str(node.state) == "UP"
    node.state = NodeState.DOWN
    assert str(node.state) == "DOWN"

@pytest.mark.parametrize("state", [
    "UP",
    "up",
    "something unexpected",
])
def test_node_raises_on_bad_state(state):
    with pytest.raises(ValueError):
        Node(id="something", state=state)

def test_nodes_are_deduplicated():
    collection = set()
    collection.add(Node(**EXAMPLE_NODE_ARGS))
    collection.add(Node(**EXAMPLE_NODE_ARGS))
    assert len(collection) == 1
