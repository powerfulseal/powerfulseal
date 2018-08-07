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
import threading
import time

from mock import MagicMock

from powerfulseal.policy import PolicyRunner
from powerfulseal.web.server import ThreadedPolicyRunner


def test_threaded_policy_runner():
    # Mock all the methods which will be called by the policy runner
    test_node_scenario = MagicMock()
    test_node_scenario.execute = MagicMock()
    test_pod_scenario = MagicMock()
    test_pod_scenario.execute = MagicMock()
    test_inventory = MagicMock()
    test_inventory.sync = MagicMock(return_value=None)

    policy = {
        'config': {
            'minSecondsBetweenRuns': 0,
            'maxSecondsBetweenRuns': 2
        }
    }
    assert PolicyRunner.is_policy_valid(policy)

    test_node_scenario.execute.assert_not_called()
    test_pod_scenario.execute.assert_not_called()
    test_inventory.sync.assert_not_called()

    # As the threaded policy runner runs on a separate thread, this can be tested
    # by waiting a reasonably short amount of time for the runner loop to run
    # and checking whether the expected functions have been called by the runner
    policy_runner = ThreadedPolicyRunner(policy, test_inventory, None, None, None, threading.Event())
    policy_runner.node_scenarios = [test_node_scenario]
    policy_runner.pod_scenarios = [test_pod_scenario]

    policy_runner.start()
    time.sleep(3)
    policy_runner.stop()
    policy_runner.join()

    assert policy_runner.stop_event
    test_node_scenario.execute.assert_called()
    test_pod_scenario.execute.assert_called()
    test_inventory.sync.assert_called()
    assert test_node_scenario.execute.call_count == test_pod_scenario.execute.call_count == test_inventory.sync.call_count
