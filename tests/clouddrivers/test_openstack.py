from mock import MagicMock
import pytest

from powerfulseal.clouddrivers.open_stack_driver import (
    get_all_ips,
)


@pytest.fixture
def example_servers():
    server1 = MagicMock()
    server1.addresses = dict(
        group1=[dict(addr="1.2.3.4")],
        group2=[dict(addr="11.22.33.44")],
        group_no_addr=[dict()],
        empty_group=[],
    )
    return [server1]


def test_get_all_ips(example_servers):
    server = example_servers[0]
    res = get_all_ips(server)
    assert res == ["1.2.3.4", "11.22.33.44"]
