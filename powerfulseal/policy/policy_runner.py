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


import random
import time

import jsonschema
import yaml
import pkgutil
import logging
from .pod_scenario import PodScenario
from .node_scenario import NodeScenario

logger = logging.getLogger(__name__)


class PolicyRunner():
    """ Reads, validates and executes a JSON schema-compliant policy
    """
    DEFAULT_POLICY = {}

    @classmethod
    def get_schema(cls):
        """ Reads the schema from the file
        """
        data = pkgutil.get_data(__name__, "ps-schema.json")
        return yaml.safe_load(data)

    @classmethod
    def load_file(cls, filename):
        with open(filename, "r") as f:
            return yaml.safe_load(f.read())

    @classmethod
    def is_policy_valid(cls, policy, schema=None):
        schema = schema or cls.get_schema()
        try:
            jsonschema.validate(policy, schema)
        except jsonschema.ValidationError as error:
            logger.error(error)
            return False
        return True

    @classmethod
    def run(cls, policy, inventory, k8s_inventory, driver, executor,
            metric_collector=None):
        """ Runs a policy forever
        """
        config = policy.get("config", {})
        wait_min = config.get("minSecondsBetweenRuns", 0)
        wait_max = config.get("maxSecondsBetweenRuns", 300)
        loops = config.get("loopsNumber", None)
        node_scenarios = [
            NodeScenario(
                name=item.get("name"),
                schema=item,
                inventory=inventory,
                driver=driver,
                executor=executor,
                metric_collector=metric_collector
            )
            for item in policy.get("nodeScenarios", [])
        ]
        pod_scenarios = [
            PodScenario(
                name=item.get("name"),
                schema=item,
                inventory=inventory,
                k8s_inventory=k8s_inventory,
                executor=executor,
                metric_collector=metric_collector
            )
            for item in policy.get("podScenarios", [])
        ]
        while loops is None or loops > 0:
            for scenario in node_scenarios:
                scenario.execute()
            for scenario in pod_scenarios:
                scenario.execute()
            sleep_time = int(random.uniform(wait_min, wait_max))
            logger.info("Sleeping for %s seconds", sleep_time)
            time.sleep(sleep_time)
            inventory.sync()
            if loops is not None:
                loops -= 1
        logger.info("All done here!")
        return node_scenarios, pod_scenarios
