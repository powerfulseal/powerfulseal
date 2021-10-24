
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

DEFAULT_TOXIPROXY_IMAGE = "docker.io/shopify/toxiproxy:2.1.4"
DEFAULT_IPTABLES_IMAGE = "gaiadocker/iproute2:latest"

class ModifyServiceAction:
  """
  Executes a http://jsonpatch.com/ object modify on a service
  """
  def __init__(self, type, name, namespace, k8s_inventory, logger=None):
    self.type = type
    self.name = name
    self.namespace = namespace
    self.k8s_inventory = k8s_inventory
    self.logger = logger or makeLogger(__name__)

  def execute(self):
    body = [{"op": self.type, "path": "/spec/selector/chaos", "value": "true"}]
    try:
      response = self.k8s_inventory.k8s_client.client_corev1api.patch_namespaced_service(name, namespace, body)
      self.logger.debug("Response %s", response)
      self.logger.info("Service modified successfully: %s %s in %s", self.type, self.name, self.namespace)
    except:
      self.logger.exception("Error modifying service: %s %s in %s", self.type, self.name, self.namespace)
      return False

class DeleteDeploymentAction():
  def __init__(self, name, namespace, k8s_inventory, logger=None):
    self.name = name
    self.namespace = namespace
    self.k8s_inventory = k8s_inventory
    self.logger = logger or makeLogger(__name__)

  def execute(self):
    try:
      response = self.k8s_inventory.k8s_client.delete_deployment(
        namespace=self.namespace,
        name=self.name,
      )
      self.logger.debug("Response %s", response)
      self.logger.info("Clone deployment deleted successfully: %s in %s", self.name, self.namespace)
    except:
      self.logger.exception("Error deleting clone deployment: %s in %s", self.name, self.namespace)
      return False

class ActionClone(ActionAbstract):

  def __init__(self, name, schema, k8s_inventory, logger=None, metric_collector=None):
    self.name = name
    self.schema = schema
    self.k8s_inventory = k8s_inventory
    self.logger = logger or makeLogger(__name__, name)
    self.metric_collector = metric_collector or StdoutCollector()
    self.cleanup_actions = []

  def get_cleanup_actions(self):
    return self.cleanup_actions

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

  def modify_services(self):
    # If we're routing all traffic to chaos replacement, modify the selector
    for service in self.schema.get("servicesToRetarget", []):
      # handle the service selector lookup
      spec = service.get("service")
      if spec is not None:
        try:
          # get the service we're after
          name = spec.get("name")
          namespace = spec.get("namespace")
          service = self.k8s_inventory.k8s_client.get_service(
            name=name,
            namespace=namespace,
          )  # Validates service exists

          ModifyServiceAction(
            type="add",
            name=name,
            namespace=namespace,
            k8s_inventory=self.k8s_inventory,
          ).execute()

          # add a cleanup action to revert the service when we're done
          self.cleanup_actions.append(
            ModifyServiceAction(
              type="remove",
              name=name,
              namespace=namespace,
              k8s_inventory=self.k8s_inventory,
            )
          )
        except:
          return False
  
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

      # handle the toxiproxy mutation
      spec = mutation.get("toxiproxy")
      if spec is not None:
        self.mutate_toxiproxy(body, spec)

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
      self.logger.exception("Failed create deploy response %s", response)
      return False

    # re-route services to target chaos labeled k8s kinds
    if not self.modify_services():
      # We want to modify services after we start the chaos clone,
      # but we want to cleanup services to point to the original before we delete the clones
      return False

    # add a cleanup action to remove the clone when we're done
    self.cleanup_actions.append(
      DeleteDeploymentAction(
        name=body.metadata.name,
        namespace=body.metadata.namespace,
        k8s_inventory=self.k8s_inventory,
      )
    )

    return True

  def mutate_traffic_control(self, body, spec):
    """
      This will modify only the container's networking (not the host) using the linux tc utility
      It will use an init container if the aim is to inherit a degraded environment
      and will create a side-car that can be delayed to wait for startup
    """
    delay = max(spec.get("delay", 0), 0)  # used for initialDelaySeconds
    if delay == 0:  # default init for backwards compatibility
      containers_ref = body.spec.template.spec.init_containers
      if containers_ref is None:
        containers_ref = []
      chaos_name = "chaos-setup-"+str(1+len(containers_ref))
    else:  # create sidecar container with delay
      containers_ref = body.spec.template.spec.containers
      chaos_name = "chaos-tc-"+str(1+len(containers_ref)) # assumes we only ever append to our containers!

    # TODO: add capability to overload probes to add wait_for scripts

    # add the tc attack to either init or containers
    if spec.get("command"):
      containers_ref.append(
        kubernetes.client.V1Container(
          name=chaos_name,
          command=spec.get("command"),
          args=spec.get("args"),
          image=spec.get("image"),
          # initialDelaySeconds=delay,
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

  def mutate_toxiproxy(self, body, spec):
    """
      This plugs a toxiproxy in as a side-car
      It also uses an init container with iptables to reroute
    """
    # 1. Precompute the ports that need to be proxied
    # for every port specified in the containers' definitions
    containers_ports = []
    for container in body.spec.template.spec.containers:
      for port in container.ports:
        containers_ports.append(port.container_port)
    containers_mapping = dict()
    # add a mapping port, that starts at 10000
    counter = 10000
    for port in containers_ports:
      while counter in containers_ports or counter in containers_mapping.values():
        counter += 1
      containers_mapping[port] = counter

    # 2. Prepare proxies in the toxiproxy format
    proxies = spec.get("proxies", [])
    for ingress_port, proxy_port in containers_mapping.items():
      proxies.append(dict(
        name="auto%s" % ingress_port,
        listen="0.0.0.0:%s" % proxy_port,
        upstream="127.0.0.1:%s" % ingress_port,
        ingress_port=ingress_port,
      ))

    # 3. Prepare the Toxiproxy setup command through the startup probe
    toxiproxy_cli = spec.get("toxiproxyCli", "/go/bin/toxiproxy-cli")
    populate_cmd = "true"
    for proxy in proxies:
      populate_cmd += " && {cli} create {name} -l {listen} -u {upstream}".format(
        cli=toxiproxy_cli,
        **proxy
      )
    toxics = spec.get("toxics", [])
    for toxic in toxics:
      # if the user specifies directly port, assume they mean the autogenerated one
      name = toxic.get("targetProxy")
      try:
        parsed = int(name)
        name = "auto" + name
      except ValueError:
        pass
      populate_cmd += " && {cli} toxic add {name} -t {type} {attributes}".format(
        cli=toxiproxy_cli,
        name=name,
        type=toxic.get("toxicType"),
        attributes=" ".join([
          "-a {name}={value}".format(
            **attr
          ) for attr in toxic.get("toxicAttributes", [])
        ])
      )

    # add the toxiproxy side-car container
    body.spec.template.spec.containers.append(
      kubernetes.client.V1Container(
        name="chaos-toxiproxy",
        image=spec.get("imageToxiproxy", DEFAULT_TOXIPROXY_IMAGE),
        startup_probe=kubernetes.client.V1Probe(
          _exec=kubernetes.client.V1ExecAction(
            command=["/bin/sh", "-c", populate_cmd],
          )
        ),
      )
    )

    # precompute the iptables command
    def get_port(listen_string):
      parts = listen_string.split(":")
      if len(parts) == 2:
        return parts[-1]
      return "80"
    iptables_cmd = "iptables -t filter -A INPUT -s 127.0.0.1 -j ACCEPT"
    names = []
    for proxy in proxies:
      ingress_port = proxy.get("ingress_port")
      if ingress_port is not None:
        iptables_cmd += (
          ' && iptables -t nat -A PREROUTING -i eth0'
          ' -p tcp --dport {ingress_port}'
          ' -j REDIRECT --to-port {egress_port}'
          ' -m comment --comment "{comment}"'
        ).format(
          ingress_port=str(ingress_port),
          egress_port=get_port(proxy.get("listen")),
          comment=proxy.get("name")
        )
        names.append(
          "{src}->{dst}".format(
            src=ingress_port,
            dst=get_port(proxy.get("listen")),
          )
        )
    iptables_cmd += ' && echo "iptables rules setup successfully: {names}"'.format(
      names=", ".join(names)
    )

    # add an init container with the iptables config
    if body.spec.template.spec.init_containers is None:
      body.spec.template.spec.init_containers = []
    body.spec.template.spec.init_containers.append(
      kubernetes.client.V1Container(
        name="iptables-setup",
        command=["/bin/sh", "-c", iptables_cmd],
        args=[],
        image=spec.get("imageIptables", DEFAULT_IPTABLES_IMAGE),
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
