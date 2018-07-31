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
import jsonschema
from flask import Flask

from powerfulseal.policy import PolicyRunner

# Flask instance and routes
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


class Server:
    def __init__(self, policy, inventory, k8s_inventory, driver, executor):
        self.policy = policy
        self.inventory = inventory
        self.inventory = k8s_inventory
        self.driver = driver
        self.executor = executor



    def is_policy_valid(self):
        """
        Checks whether the specified policy is valid depending on the schema
        file used in the PolicyRunner class
        """
        schema = PolicyRunner.get_schema()
        try:
            jsonschema.validate(self.policy, schema)
        except jsonschema.ValidationError:
            return False
        return True

    def start_server(self, host, port):
        app.run(host=host, port=port)
