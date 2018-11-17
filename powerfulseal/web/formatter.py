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
import copy

from powerfulseal.web.constants import *


class PolicyFormatter:
    """
    Converts between internal representation of a policy and the representation
    used by the API
    """
    @classmethod
    def output_policy(cls, policy):
        output_node_scenarios = []
        for policy_scenario in policy.get('nodeScenarios', []):
            output_node_scenarios.append(PolicyFormatter.output_node_scenario(policy_scenario))

        # Format pod scenario output for JSON output
        output_pod_scenarios = []
        for policy_scenario in policy.get('podScenarios', []):
            output_pod_scenarios.append(PolicyFormatter.output_pod_scenario(policy_scenario))

        return {
            'minSecondsBetweenRuns': policy.get('config', {}).get('minSecondsBetweenRuns', 0),
            'maxSecondsBetweenRuns': policy.get('config', {}).get('maxSecondsBetweenRuns', 300),
            'nodeScenarios': output_node_scenarios,
            'podScenarios': output_pod_scenarios
        }

    @classmethod
    def output_node_scenario(cls, policy_scenario):
        output_node_scenario = copy.deepcopy(DEFAULT_OUTPUT_NODE_SCENARIO)
        output_node_scenario['name'] = policy_scenario['name']

        # Process matchers
        for matcherItem in policy_scenario.get('match', []):
            output_node_scenario['matchers'].append(matcherItem['property'])

        # Process filters
        for filterItem in policy_scenario.get('filters', []):
            # In the schema, filter items are represented by an object with a single item

            # Process property filters
            if 'property' in filterItem:
                output_node_scenario['filters'].append(filterItem['property'])

            # Process time of execution filters
            if 'dayTime' in filterItem:
                for dayOfWeek in POLICY_DAYS_OF_WEEK:
                    output_node_scenario['dayOfWeek'][dayOfWeek] = \
                        dayOfWeek in filterItem['dayTime']['onlyDays']
                output_node_scenario['startTime'] = filterItem['dayTime']['startTime']
                output_node_scenario['endTime'] = filterItem['dayTime']['endTime']
                output_node_scenario['isTimeOfExecutionEnabled'] = True

            # Process random sample filters
            if 'randomSample' in filterItem:
                if 'size' in filterItem['randomSample']:
                    # The default scenario's other keys must not be modified or else the front-end
                    # will missed keys which are being watched
                    output_node_scenario['randomSample']['type'] = RandomSampleType.SIZE.value
                    output_node_scenario['randomSample']['size'] = filterItem['randomSample']['size']
                elif 'ratio' in filterItem['randomSample']:
                    output_node_scenario['randomSample']['type'] = RandomSampleType.RATIO.value
                    output_node_scenario['randomSample']['ratio'] = filterItem['randomSample']['ratio']

            # Process probability pass all filters
            if 'probability' in filterItem:
                output_node_scenario['probabilityPassAll']['isEnabled'] = True
                output_node_scenario['probabilityPassAll']['probability'] = \
                    filterItem['probability']['probabilityPassAll']

        # Process actions
        for actionItem in policy_scenario.get('actions', []):
            if 'stop' in actionItem:
                output_node_scenario['actions'].append({
                    'type': NodeActionType.STOP.value,
                    'params': [{
                        'name': k,
                        'value': v,
                    } for (k, v) in actionItem['stop'].items()]
                })
            elif 'start' in actionItem:
                output_node_scenario['actions'].append({
                    'type': NodeActionType.START.value,
                    'params': []
                })
            elif 'wait' in actionItem:
                output_node_scenario['actions'].append({
                    'type': NodeActionType.WAIT.value,
                    'params': [
                        {
                            'name': 'seconds',
                            'value': actionItem['wait']['seconds']
                        }
                    ]
                })
            elif 'execute' in actionItem:
                output_node_scenario['actions'].append({
                    'type': NodeActionType.EXECUTE.value,
                    'params': [
                        {
                            'name': 'cmd',
                            'value': actionItem['execute']['cmd']
                        }
                    ]
                })

        return output_node_scenario

    @classmethod
    def output_pod_scenario(cls, policy_scenario):
        output_pod_scenario = copy.deepcopy(DEFAULT_OUTPUT_POD_SCENARIO)
        output_pod_scenario['name'] = policy_scenario['name']

        # Process matchers
        output_pod_scenario['matchers'] = []
        for matcherItem in policy_scenario.get('match', []):
            if 'namespace' in matcherItem:
                output_pod_scenario['matchers'].append({
                    'type': PodMatcherTypes.NAMESPACE.value,
                    'params': [{
                        'name': k,
                        'value': v
                    } for (k, v) in matcherItem['namespace'].items()]
                })
            elif 'deployment' in matcherItem:
                output_pod_scenario['matchers'].append({
                    'type': PodMatcherTypes.DEPLOYMENT.value,
                    'params': [{
                        'name': k,
                        'value': v
                    } for (k, v) in matcherItem['deployment'].items()]
                })
            elif 'labels' in matcherItem:
                output_pod_scenario['matchers'].append({
                    'type': PodMatcherTypes.LABELS.value,
                    'params': [{
                        'name': k,
                        'value': v,
                    } for (k, v) in matcherItem['labels'].items()]
                })

        # Process filters
        output_pod_scenario['filters'] = []
        for filterItem in policy_scenario.get('filters', []):
            # Process property filters
            if 'property' in filterItem:
                output_pod_scenario['filters'].append(filterItem['property'])

            # Process time of execution filters
            if 'dayTime' in filterItem:
                for dayOfWeek in POLICY_DAYS_OF_WEEK:
                    output_pod_scenario['dayOfWeek'][dayOfWeek] = \
                        dayOfWeek in filterItem['dayTime']['onlyDays']
                output_pod_scenario['startTime'] = filterItem['dayTime']['startTime']
                output_pod_scenario['endTime'] = filterItem['dayTime']['endTime']
                output_pod_scenario['isTimeOfExecutionEnabled'] = True

            # Process random sample filters
            if 'randomSample' in filterItem:
                if 'size' in filterItem['randomSample']:
                    # The default scenario's other keys must not be modified or else the front-end
                    # will missed keys which are being watched
                    output_pod_scenario['randomSample']['type'] = RandomSampleType.SIZE.value
                    output_pod_scenario['randomSample']['size'] = filterItem['randomSample']['size']
                elif 'ratio' in filterItem['randomSample']:
                    output_pod_scenario['randomSample']['type'] = RandomSampleType.RATIO.value
                    output_pod_scenario['randomSample']['ratio'] = filterItem['randomSample']['ratio']

            # Process probability pass all filters
            if 'probability' in filterItem:
                output_pod_scenario['probabilityPassAll']['isEnabled'] = True
                output_pod_scenario['probabilityPassAll']['probability'] = \
                    filterItem['probability']['probabilityPassAll']

        # Process actions
        output_pod_scenario['actions'] = []
        for actionItem in policy_scenario.get('actions', []):
            if 'kill' in actionItem:
                output_pod_scenario['actions'].append({
                    'type': PodActionType.KILL.value,
                    'params': [{
                        'name': k,
                        'value': v,
                    } for (k, v) in actionItem['kill'].items()]
                })
            elif 'wait' in actionItem:
                output_pod_scenario['actions'].append({
                    'type': PodActionType.WAIT.value,
                    'params': [
                        {
                            'name': 'seconds',
                            'value': actionItem['wait']['seconds']
                        }
                    ]
                })

        return output_pod_scenario

    @classmethod
    def parse_policy(cls, input_policy):
        """
        :raises KeyError on parse failure
        """
        return {
            'config': {
                'minSecondsBetweenRuns': input_policy.get('minSecondsBetweenRuns'),
                'maxSecondsBetweenRuns': input_policy.get('maxSecondsBetweenRuns')
            },
            'nodeScenarios': [
                PolicyFormatter.parse_node_scenario(node_scenario)
                for node_scenario in input_policy.get('nodeScenarios', [])
            ],
            'podScenarios': [
                PolicyFormatter.parse_pod_scenario(pod_scenario)
                for pod_scenario in input_policy.get('podScenarios', [])
            ]
        }

    @classmethod
    def parse_node_scenario(cls, input_scenario):
        """
        :raises KeyError on parse failure
        """
        policy_scenario = {
            'name': input_scenario['name']
        }

        # Process matchers
        policy_scenario['match'] = []
        for matcher in input_scenario.get('matchers', []):
            policy_scenario['match'].append({
                'property': matcher
            })

        # Process filter properties
        policy_scenario['filters'] = []
        for filter in input_scenario.get('filters', []):
            policy_scenario['filters'].append({
                'property': filter
            })

        # Process time of execution filters
        if input_scenario.get('isTimeOfExecutionEnabled'):
            policy_scenario['filters'].append({
                'dayTime': {
                    'onlyDays': [dayOfWeek for dayOfWeek in POLICY_DAYS_OF_WEEK if
                                 input_scenario['dayOfWeek'][dayOfWeek]],
                    'startTime': input_scenario['startTime'],
                    'endTime': input_scenario['endTime']
                }
            })

        # Process random sample
        if input_scenario['randomSample']['type'] == RandomSampleType.SIZE.value:
            policy_scenario['filters'].append({
                'randomSample': {
                    'size': input_scenario['randomSample']['size']
                }
            })
        elif input_scenario['randomSample']['type'] == RandomSampleType.RATIO.value:
            policy_scenario['filters'].append({
                'randomSample': {
                    'ratio': input_scenario['randomSample']['ratio']
                }
            })

        # Process probability pass all
        if input_scenario['probabilityPassAll']['isEnabled']:
            policy_scenario['filters'].append({
                'probability': {
                    'probabilityPassAll': input_scenario['probabilityPassAll']['probability']
                }
            })

        # Process actions
        policy_scenario['actions'] = []
        for action in input_scenario.get('actions', []):
            policy_scenario['actions'].append({
                NODE_ACTION_TYPE_NAMES[action['type']]: {param['name']: param['value'] for param in action['params']}
            })

        return policy_scenario

    @classmethod
    def parse_pod_scenario(cls, input_scenario):
        policy_scenario = {
            'name': input_scenario['name']
        }

        # Process matchers
        policy_scenario['match'] = []
        for matcher in input_scenario.get('matchers', []):
            if matcher['type'] == PodMatcherTypes.NAMESPACE.value:
                policy_scenario['match'].append({
                    'namespace': {param['name']: param['value'] for param in matcher['params']}
                })
            elif matcher['type'] == PodMatcherTypes.DEPLOYMENT.value:
                policy_scenario['match'].append({
                    'deployment': {param['name']: param['value'] for param in matcher['params']}
                })
            elif matcher['type'] == PodMatcherTypes.LABELS.value:
                policy_scenario['match'].append({
                    'labels': {param['name']: param['value'] for param in matcher['params']}
                })

        # Process filter properties
        policy_scenario['filters'] = []
        for filter_item in input_scenario.get('filters', []):
            policy_scenario['filters'].append({
                'property': filter_item
            })

        # Process time of execution filters
        if input_scenario['isTimeOfExecutionEnabled']:
            policy_scenario['filters'].append({
                'dayTime': {
                    'onlyDays': [dayOfWeek for dayOfWeek in POLICY_DAYS_OF_WEEK if
                                 input_scenario['dayOfWeek'][dayOfWeek]],
                    'startTime': input_scenario['startTime'],
                    'endTime': input_scenario['endTime']
                }
            })

        # Process random sample
        if input_scenario['randomSample']['type'] == RandomSampleType.SIZE.value:
            policy_scenario['filters'].append({
                'randomSample': {
                    'size': input_scenario['randomSample']['size']
                }
            })
        elif input_scenario['randomSample']['type'] == RandomSampleType.RATIO.value:
            policy_scenario['filters'].append({
                'randomSample': {
                    'ratio': input_scenario['randomSample']['ratio']
                }
            })

        # Process probability pass all
        if input_scenario['probabilityPassAll']['isEnabled']:
            policy_scenario['filters'].append({
                'probability': {
                    'probabilityPassAll': input_scenario['probabilityPassAll']['probability']

                }
            })

        # Process actions
        policy_scenario['actions'] = []
        for action in input_scenario['actions']:
            policy_scenario['actions'].append({
                POD_ACTION_TYPE_NAMES[action['type']]: {param['name']: param['value'] for param in action['params']}
            })

        return policy_scenario
