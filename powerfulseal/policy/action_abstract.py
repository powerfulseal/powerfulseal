
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


import time
import re
from datetime import datetime
import calendar
import random
from powerfulseal import makeLogger

from abc import ABC, abstractmethod
from ..metriccollectors.stdout_collector import StdoutCollector


class ActionAbstract(ABC):

    @abstractmethod
    def execute(self):
        """
            Executes the actual action
        """
        return True # pragma: no cover

    def get_cleanup_actions(self):
        """
            If the job requires cleanup, return actions necessary to do the cleanup.
        """
        return [] # pragma: no cover