
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


from enum import IntEnum


class NodeState(IntEnum):
    """
        Enumeration to describe a Node state
    """
    UNKNOWN = 1
    UP = 2
    DOWN = 3

    def __str__(self):
        return '{0}'.format(self.name)


class Node(object):
    """
        Basic class representing a machine in the cluster
    """


    def __init__(self, id, name=None, ip=None, extIp=None, az=None,
            groups=None, no=None, state=None):
        self.id = id
        self.name = name
        self.ip = ip
        self.extIp = extIp
        self.az = az
        self.groups = groups or []
        self.no = no
        if state is None:
            self.state = NodeState.UNKNOWN
        elif type(state) is not NodeState:
            raise ValueError("Please use a NodeState; %s provided" % state)
        else:
            self.state = state

    def __str__(self):
        return (
            "[node no={no} id={id} ip={ip} extIp={extIp} az={az} groups={groups} name={name} "
            "state={state}]"
        ).format(
            no=self.no,
            id=self.id,
            name=self.name,
            ip=self.ip,
            extIp=self.extIp,
            az=self.az,
            groups=self.groups,
            state=str(self.state)
        )

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return other.id == self.id

    def __hash__(self):
        return hash(self.id)
