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
import json

import mock
import pytest

from powerfulseal.k8s.heapster_client import HeapsterClient


def test_get_pod_metrics():
    heapster = HeapsterClient(None)

    def mocked_response(*args):
        mocked = mock.MagicMock()
        mocked.status_code = 200
        mocked.json = lambda: json.loads("""
{
  "metadata": {},
  "items": [
    {
      "metadata": {
        "name": "abc",
        "namespace": "default"
      },
      "containers": [
        {
          "name": "container-1a",
          "usage": {
            "cpu": "1m",
            "memory": "68896Ki"
          }
        },
        {
          "name": "container-1b",
          "usage": {
            "cpu": "1m",
            "memory": "2Ki"
          }
        }
      ]
    },
    {
      "metadata": {
        "name": "def",
        "namespace": "default"
      },
      "containers": [
        {
          "name": "container-2a",
          "usage": {
            "cpu": "3m",
            "memory": "36840Ki"
          }
        }
      ]
    }
  ]
}
          """)
        return mocked

    with mock.patch('powerfulseal.k8s.heapster_client.requests.get',
                    side_effect=mocked_response):
        result = heapster.get_pod_metrics()
        assert len(result) == 1 and 'default' in result
        assert len(result['default']) == 2
        assert result == {
            'default': {
                'abc': {
                    'cpu': 0.002,
                    'memory': 68898000
                },
                'def': {
                    'cpu': 0.003,
                    'memory': 36840000
                }
            }
        }


def test_parse_cpu_string():
    heapster = HeapsterClient(None)
    assert heapster.parse_cpu_string('1') == pytest.approx(1)
    assert heapster.parse_cpu_string('100') == pytest.approx(100)
    assert heapster.parse_cpu_string('1m') == pytest.approx(0.001)
    assert heapster.parse_cpu_string('10m') == pytest.approx(0.01)


def test_parse_memory_string():
    heapster = HeapsterClient(None)
    assert heapster.parse_memory_string('68896') == 68896
    assert heapster.parse_memory_string('68896Mi') == 68896000000
    assert heapster.parse_memory_string('68896Ki') == 68896000
    assert heapster.parse_memory_string('68Gi') == 68000000000
    assert heapster.parse_memory_string('2Ti') == 2000000000000
    assert heapster.parse_memory_string('1') == 1
    assert heapster.parse_memory_string('0') == 0
    assert heapster.parse_memory_string('16') == 16

    with pytest.raises(NotImplementedError) as _:
        heapster.parse_memory_string('6889M')

    with pytest.raises(ValueError) as _:
        heapster.parse_memory_string('688M9')

    with pytest.raises(KeyError) as _:
        heapster.parse_memory_string('688Ei')
