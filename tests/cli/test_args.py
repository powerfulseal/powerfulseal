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

from os.path import expanduser
from powerfulseal.cli.__main__ import parse_args

HOME = expanduser("~")


def test_validate_policy_file_does_not_require_other_arguments():
    parser = parse_args([
        'validate',
        '--policy-file', 'test/config.yml'
    ])
    assert parser.mode == "validate"
    assert parser.policy_file == 'test/config.yml'
    
def test_kubeconfig_default():
    parser = parse_args([
        'interactive',
        '--inventory-kubernetes',
        '--no-cloud'
    ])
    assert parser.kubeconfig is None


def test_interactive_mode_integration():
    parser = parse_args([
        'interactive',
        '--inventory-kubernetes',
        '--kubeconfig', '~/.kube/config',
        '--no-cloud'
    ])
    assert parser.mode == "interactive"
    assert parser.inventory_kubernetes
    assert parser.kubeconfig == HOME + '/.kube/config'
    assert parser.no_cloud


def test_autonomous_mode_integration():
    parser = parse_args([
        'autonomous',
        '--inventory-kubernetes',
        '--kubeconfig', '~/config',
        '--no-cloud',
        '--policy-file', '~/policy.yml'
    ])
    assert parser.mode == "autonomous"
    assert parser.inventory_kubernetes
    assert parser.kubeconfig == HOME + '/config'
    assert parser.no_cloud
    assert parser.policy_file == '~/policy.yml'
