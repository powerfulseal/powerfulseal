
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

import requests
import time

from powerfulseal import makeLogger

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_abstract import ActionAbstract


class ActionClone(ActionAbstract):

  def __init__(self, name, schema, k8s_inventory, logger=None, metric_collector=None):
    self.name = name
    self.schema = schema
    self.k8s_inventory = k8s_inventory
    self.logger = logger or makeLogger(__name__, name)
    self.metric_collector = metric_collector or StdoutCollector()

  def get_source_schema(self, source):
    # currently, only deployments are supported
    source_deployment = source.get("deployment")
    deployment = self.k8s_inventory.k8s_client.get_deployment(
      name=source_deployment.get("name"),
      namespace=source_deployment.get("namespace"),
    )
    return deployment

  def execute(self):
    replicas = self.schema.get("replicas", 1)
    source = self.schema.get("source")
    labels = self.schema.get("labels", {})
    mutations = self.schema.get("mutations", {})

    # get the source deployment
    try:
      source_schema = self.get_source_schema(source)
    except:
      return False

    # apply the desired replicas number

    # apply the desired labels

    # apply the desired mutations

    # create the new, cloned deployment
    print(replicas, source, labels, mutations)
    print(source_schema)

    # add a cleanup action to remove the clone

    return True
