
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
import kubernetes.client

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

  def modify_labels(self, body, update_labels):
    """
      Modifies labels and deployment selectors as required by the schema
    """
    for label_modifier in self.schema.get("labels", []):

      # handle the service selector lookup
      spec = label_modifier.get("service")
      if spec is not None:
        try:
          # get the service we're after
          service = self.k8s_inventory.k8s_client.get_service(
            name=spec.get("name"),
            namespace=spec.get("namespace"),
          )
          # reset the existing labels
          update_labels()
          # update with the selectors from the service
          update_labels(**service.spec.selector)
        except:
          return False

      # handle the static label modifications
      spec = label_modifier.get("label")
      if spec is not None:
        updates = dict()
        updates[spec.get("key")] = spec.get("value")
        update_labels(**updates)

    return body

  def execute(self):
    # get the source deployment
    try:
      source_schema = self.get_source_schema(self.schema.get("source"))
    except:
      return False

    # build the body for the request to create
    body = kubernetes.client.V1Deployment()
    body.metadata = kubernetes.client.V1ObjectMeta(
      name=source_schema.metadata.name + "-chaos",
      namespace=source_schema.metadata.namespace,
      annotations=dict(
        original_deployment=source_schema.metadata.name,
        chaos_scenario=self.name,
      ),
      labels = dict(
        chaos="true",
      ),
    )
    body.spec = kubernetes.client.V1DeploymentSpec(
      replicas=self.schema.get("replicas", 1),
      selector=source_schema.spec.selector,
      template=source_schema.spec.template,
    )

    if body.spec.selector.match_expressions is not None:
      self.logger.error("Deployment is using match_expressions. Not supported")
      return False

    # handle the labels modifiers
    def update_labels(**kwargs):
      if not kwargs:
        body.spec.selector.match_labels = dict()
        body.spec.template.metadata.labels = dict()
      for key, value in kwargs.items():
        body.spec.selector.match_labels[key] = value
        body.spec.template.metadata.labels[key] = value
    self.modify_labels(body, update_labels)

    # handle the mutations
    for mutation in self.schema.get("mutations", []):

      # handle the environment mutation
      spec = mutation.get("environment")
      if spec is not None:
        for container in body.spec.template.spec.containers:
          container.env.append(
            kubernetes.client.V1EnvVar(
              name=spec.get("name"),
              value=spec.get("value"),
            )
          )

      # handle the tc mutation
      spec = mutation.get("tc")
      if spec is not None:
        self.mutate_traffic_control(body, spec)

      # TODO handle the toxiproxy mutation
      pass

    # always insert the extra selector
    update_labels(chaos="true")

    # create the clone
    try:
      self.logger.debug("Body %s", body)
      response = self.k8s_inventory.k8s_client.create_deployment(
        namespace=body.metadata.namespace,
        body=body,
      )
      self.logger.debug("Response %s", response)
      self.logger.info("Clone deployment created successfully")
    except:
      return False

    # TODO add a cleanup action to remove the clone

    return True


  def mutate_traffic_control(self, body, spec):
    """ Adds an init container with tc """
    if body.spec.template.spec.init_containers is None:
      body.spec.template.spec.init_containers = []
    body.spec.template.spec.init_containers.append(
      kubernetes.client.V1Container(
        name="chaos"+str(1+len(body.spec.template.spec.init_containers)),
        command=spec.get("command"),
        args=spec.get("args"),
        image=spec.get("image"),
        security_context=kubernetes.client.V1SecurityContext(
          run_as_user=spec.get("user"),
          capabilities=kubernetes.client.V1Capabilities(
            add=[
              "NET_ADMIN"
            ]
          )
        )
      )
    )
