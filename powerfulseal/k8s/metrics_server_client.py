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
from powerfulseal import makeLogger

import requests

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

POD_METRICS_PATH = "/apis/metrics.k8s.io/v1beta1/pods"

# Value is a fraction of a single CPU core (e.g., 1n = 1 / 1000000000 => 0.000000001)
CPU_UNITS = {'n': 1000000000}
# Value is a multiple of a byte (e.g., 1Ki => 1000)
MEMORY_UNITS = {'Ki': 1000, 'Mi': 1000000, 'Gi': 1000000000, 'Ti': 1000000000000, 'Pi': 1000000000000000}


class MetricsServerClient:
    """
    Retrieves CPU and memory metrics from metrics-server
    """

    def __init__(self, base_path, logger=None):
        self.base_path = base_path or ''
        self.logger = logger or makeLogger(__name__)

    def get_pod_metrics(self):
        response = requests.get(self.base_path + POD_METRICS_PATH)
        if response.status_code != 200:
            self.logger.error("Could not retrieve pod metrics. Exiting.")
            exit()

        try:
            data = response.json()
        except ValueError:
            self.logger.error("Unable to retrieve response data. Exiting.")
            exit()

        # Key: map of namespaces; value: map of pods
        metrics = {}
        for item in data['items']:
            namespace = item['metadata']['namespace']
            name = item['metadata']['name']
            cpu = sum(map(lambda c: self.parse_cpu_string(c['usage']['cpu']), item['containers']))
            memory = sum(map(lambda c: self.parse_memory_string(c['usage']['memory']), item['containers']))

            if namespace not in metrics:
                metrics[namespace] = {}

            metrics[namespace][name] = {
                'cpu': cpu,
                'memory': memory
            }

        return metrics

    def parse_cpu_string(self, cpu):
        """
        Returns CPU in number of cores (e.g., "120n" => 0.0000012)
        """
        if len(cpu) < 2 or is_numeric(cpu[-1]):
            return float(cpu)

        return float(cpu[:-1]) / CPU_UNITS[cpu[-1:]]

    def parse_memory_string(self, memory):
        """
        Returns memory in number of bytes (e.g., "228Ki" => 228000)
        """
        if len(memory) < 2:
            return int(memory)

        is_last_numeric = is_numeric(memory[-1])
        is_penultimate_numeric = is_numeric(memory[-2])
        if is_penultimate_numeric and is_last_numeric:
            # Memory is already in bytes
            return int(memory)
        elif not is_penultimate_numeric and is_last_numeric:
            # Impossible case of alphabetical followed by numeric
            raise ValueError("Memory is malformed")
        elif is_penultimate_numeric and not is_last_numeric:
            # Unimplemented case of single-character suffixes (it is unknown
            # whether metric-server implements this). Currently, memory is handled
            # with power-of-two suffixes (e.g., Ki, Mi, etc.)
            raise NotImplementedError("Single character units are not implemented")
        else:
            return int(memory[:-2]) * MEMORY_UNITS[memory[-2:]]


def is_numeric(c):
    return '0' <= c <= '9'
