
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


import pkg_resources
import pytest
from powerfulseal.node.inventory import read_inventory_file_to_dict


def test_reads_sample_inventory():
    filename = pkg_resources.resource_filename('tests.node', 'example_inventory')
    groups = read_inventory_file_to_dict(filename)
    assert groups["groupa"] == ["192.168.1.1"]
    assert groups["groupb"] == ["192.168.2.1"]
    assert groups["groupc"] == ["192.168.3.1"]
    assert groups["workers:children"] == list(set(["192.168.1.1","192.168.2.1","192.168.3.1"]))
