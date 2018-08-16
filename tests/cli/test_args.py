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

from powerfulseal.cli.__main__ import parse_args


def test_validate_policy_file_does_not_require_other_arguments():
    parser = parse_args(['--validate-policy-file', 'test/config.yml'])
    assert parser.validate_policy_file == 'test/config.yml'


def test_interactive_mode_integration():
    parser = parse_args(['--inventory-kubernetes', '--kube-config',
                        '~/.kube/config', '--no-cloud', '--interactive'])
    assert parser.inventory_kubernetes
    assert parser.kube_config == '~/.kube/config'
    assert parser.no_cloud
    assert parser.interactive


def test_autonomous_mode_integration():
    parser = parse_args(['--inventory-kubernetes', '--kube-config',
                        '~/.kube/config', '--no-cloud', '--run-policy-file',
                        '~/policy.yml', '--inventory-kubernetes'])
    assert parser.inventory_kubernetes
    assert parser.kube_config == '~/.kube/config'
    assert parser.no_cloud
    assert parser.run_policy_file == '~/policy.yml'
    assert parser.inventory_kubernetes
