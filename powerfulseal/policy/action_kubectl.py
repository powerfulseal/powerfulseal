
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

import logging

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_abstract import ActionAbstract


class ActionKubectl(ActionAbstract):

    def __init__(self, name, schema, logger=None, metric_collector=None):
        self.name = name
        self.schema = schema
        self.logger = logger or logging.getLogger(__name__ + "." + name)
        self.metric_collector = metric_collector or StdoutCollector()

    def execute(self):
        pass