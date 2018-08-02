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


import abc, six


@six.add_metaclass(abc.ABCMeta)
class AbstractDriver():
    """
        Abstract class representing a cloud driver.
        All concrete drivers should implement this.
    """

    @abc.abstractmethod
    def sync(self):
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_by_ip(self, ip):
        pass  # pragma: no cover

    @abc.abstractmethod
    def stop(self, node):
        pass  # pragma: no cover

    @abc.abstractmethod
    def start(self, node):
        pass  # pragma: no cover

    @abc.abstractmethod
    def delete(self, node):
        pass  # pragma: no cover
