
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


import configparser

ConfigParser = configparser.ConfigParser


def read_inventory_file_to_dict(inventory_filename):
    """ Reads inventory file in ini format (for example in Ansible format),
        returns a dictionary, where keys correspond to lower case sections,
        and resolved first level-inclusions
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(inventory_filename)
    # extract the IPs into lower-case groups per section
    _groups = {
        key.lower(): [ ip.lower().split(" ")[0] for (ip, group) in config.items(key)]
        for key in config.sections()
    }
    # resolve one level groups hierarchy
    groups = {}
    for group, ips in _groups.items():
        ips_set = set()
        for ip in ips:
            subgroup = _groups.get(ip)
            if subgroup is not None:
                for sub in subgroup:
                    ips_set.add(sub)
            else:
                ips_set.add(ip)
        groups[group] = list(ips_set)
    return groups
