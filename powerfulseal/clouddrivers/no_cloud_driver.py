
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


from powerfulseal import makeLogger
from . import AbstractDriver
from ..node import Node, NodeState

MESSAGE_IM_NO_CLOUD_DRIVER = (
"Trying to %s things while using a no-cloud driver. "
"If you don't expect to be seeing this, you might want"
" to rethink some of your choices"
)


class NoCloudDriver(AbstractDriver):
    """
        Concrete implementation of a noop driver
    """

    def __init__(self, logger=None):
        self.logger = logger or makeLogger(__name__)

    def sync(self):
        """ Noop
        """
        self.logger.debug(
            MESSAGE_IM_NO_CLOUD_DRIVER, "sync"
        )

    def get_by_ip(self, ip):
        """ Creates a Node instance for given IP.
        """
        return Node(
            id="fake-{ip}".format(ip=ip),
            ip=ip,
            extIp=ip,
            az="nope",
            name="local-{ip}".format(ip=ip),
            state=NodeState.UNKNOWN
        )

    def stop(self, node):
        """ Noop
        """
        self.logger.error(
            MESSAGE_IM_NO_CLOUD_DRIVER, "stop"
        )

    def start(self, node):
        """ Noop
        """
        self.logger.error(
            MESSAGE_IM_NO_CLOUD_DRIVER, "start"
        )

    def delete(self, node):
        """ Noop
        """
        self.logger.error(
            MESSAGE_IM_NO_CLOUD_DRIVER, "delete"
        )

