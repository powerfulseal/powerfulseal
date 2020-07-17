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
import sys
import copy

import jsonschema
import yaml
import pkgutil
from powerfulseal import makeLogger
from .scenario import Scenario

logger = makeLogger(__name__)


class PolicyRunner():
    """ Reads, validates and executes a JSON schema-compliant policy
    """
    DEFAULT_POLICY = {
        "scenarios": []
    }

    def __init__(self, config_file, k8s_client, logger=None):
        self.config_file = config_file
        self.k8s_client = k8s_client
        self.logger = logger or makeLogger(__name__)

    def read_policy(self):
        """
            Read configuration
        """
        if self.config_file is None:
            policy = copy.deepcopy(PolicyRunner.DEFAULT_POLICY)
        else:
            policy = PolicyRunner.load_file(self.config_file)

        # Load scenarios from K8S crd extending file scenarios
        scenarios = self.k8s_client.get_scenarios()
        policy['scenarios'].extend(scenarios)
        if not PolicyRunner.is_policy_valid(policy):
            self.logger.error("Policy not valid. See log output above.")
            return sys.exit(1)
        return policy

    @classmethod
    def get_schema(cls):
        """ Reads the schema from the file
        """
        data = pkgutil.get_data(__name__, "ps-schema.yaml")
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
            logger.error(policy)
            logger.error(error)
            return False
        return True

    def run(self, inventory, k8s_inventory, driver, executor,
            metric_collector=None):
        """ Runs a policy forever
        """
        policy = self.read_policy()
        loops = policy.get("config", {}).get("runStrategy", {}).get("runs", None)
        while loops is None or loops > 0:
            policy = self.read_policy()
            config = policy.get("config", {}).get("runStrategy", {})
            should_randomize = config.get("strategy") == "random"
            wait_min = config.get("minSecondsBetweenRuns", 0)
            wait_max = config.get("maxSecondsBetweenRuns", 300)
            exitConfig = policy.get("config", {}).get("exitStrategy", {})
            exitStrategy = exitConfig.get("strategy", "report")
            scenarios = [
                Scenario(
                    name=item.get("name"),
                    schema=item,
                    inventory=inventory,
                    k8s_inventory=k8s_inventory,
                    driver=driver,
                    executor=executor,
                    metric_collector=metric_collector
                )
                for item in policy.get("scenarios", [])
            ]

            if should_randomize:
                random.shuffle(scenarios)
            for scenario in scenarios:
                ret = scenario.execute()
                if not ret:
                    if exitStrategy == "fail-fast":
                        logger.error("Exiting early")
                        return False
                    else:
                        logger.error("Scenario failed, reporting and carrying on")
            sleep_time = int(random.uniform(wait_min, wait_max))
            logger.info("Sleeping for %s seconds", sleep_time)
            time.sleep(sleep_time)
            if loops is not None:
                loops -= 1
        logger.info("All done here!")
        return True
