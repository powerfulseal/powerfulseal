# Copyright 2018 Bloomberg Finance L.P.
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

POLICY_DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


class RandomSampleType(IntEnum):
    DISABLED = 0
    SIZE = 1
    RATIO = 2


class NodeActionType(IntEnum):
    STOP = 0
    START = 1
    WAIT = 2
    EXECUTE = 3


NODE_ACTION_TYPE_NAMES = {
    NodeActionType.STOP: 'stop',
    NodeActionType.START: 'start',
    NodeActionType.WAIT: 'wait',
    NodeActionType.EXECUTE: 'execute'
}


class PodActionType(IntEnum):
    KILL = 0
    WAIT = 1


POD_ACTION_TYPE_NAMES = {
    PodActionType.KILL: 'kill',
    PodActionType.WAIT: 'wait'
}


class PodMatcherTypes(IntEnum):
    NAMESPACE = 0
    DEPLOYMENT = 1
    LABELS = 2


DEFAULT_OUTPUT_NODE_SCENARIO = {
    'name': '',
    'matchers': [],
    'filters': [],
    'actions': [],
    'dayOfWeek': {
        'monday': True,
        'tuesday': True,
        'wednesday': True,
        'thursday': True,
        'friday': True,
        'saturday': False,
        'sunday': False
    },
    'startTime': {
        'hour': 10,
        'minute': 0,
        'second': 0
    },
    'endTime': {
        'hour': 17,
        'minute': 30,
        'second': 0
    },
    'randomSample': {
        'type': RandomSampleType.DISABLED,
        'size': 5,
        'ratio': 0.2
    },
    'probabilityPassAll': {
        'isEnabled': False,
        'probability': 0.5
    },
}

DEFAULT_OUTPUT_POD_SCENARIO = {
    'name': '',
    'matchers': [],
    'filters': [],
    'isTimeOfExecutionEnabled': False,
    'dayOfWeek': {
        'monday': True,
        'tuesday': True,
        'wednesday': True,
        'thursday': True,
        'friday': True,
        'saturday': False,
        'sunday': False
    },
    'startTime': {
        'hour': 10,
        'minute': 0,
        'second': 0
    },
    'endTime': {
        'hour': 17,
        'minute': 30,
        'second': 0
    },
    'randomSample': {
        'type': RandomSampleType.DISABLED,
        'size': 5,
        'ratio': 0.2
    },
    'probabilityPassAll': {
        'isEnabled': False,
        'probability': 0.5
    },
    'actions': []
}
