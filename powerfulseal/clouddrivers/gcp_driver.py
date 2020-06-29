import json
from powerfulseal import makeLogger
import subprocess
import sys

import googleapiclient.discovery
from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials

from . import AbstractDriver
from ..node import Node
from ..node import NodeState


def create_connection_from_config():
    """ Returns Google API client for Compute. It detects credentials for Service accounts and User accounts.
    """
    credentials = ServiceAccountCredentials.get_application_default()
    return googleapiclient.discovery.build(
        'compute', 'v1', credentials=credentials,cache_discovery=False)


def get_all_ips(instance):
    """ Returns the public and private ip addresses of an GCP Compute instance
    """
    ip_list = []

    # TODO: Sometimes Compute instances lose the Public IP, so this is a
    # temporal workaround
    try:
        ip_list.append(instance["networkInterfaces"][0]
                       ["accessConfigs"][0]["natIP"])  # Public
    except Exception:
        pass

    ip_list.append(instance["networkInterfaces"][0]["networkIP"])  # Private
    return ip_list


# https://cloud.google.com/compute/docs/instances/instance-life-cycle
MAPPING_STATES_STATUS = {
    "RUNNING": NodeState.UP,
    "STOPPED": NodeState.DOWN,
    "TERMINATED": NodeState.DOWN,
}


def server_status_to_state(status):
    return MAPPING_STATES_STATUS.get(status.upper(), NodeState.UNKNOWN)


def create_node_from_server(server):
    """ Translate GCP Compute Instance representation into a Node object.
    """
    # TODO: Sometimes Compute instances lose the Public IP, so this is a
    # temporal workaround
    try:
        public_ip = server["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
    except Exception:
        public_ip = 'None'

    return Node(
        id=server['id'],
        ip=server["networkInterfaces"][0]["networkIP"],
        extIp=public_ip,
        az=server['zone'].rsplit('/', 1)[1],
        name=server['name'],
        state=server_status_to_state(server['status']),
    )


def get_zones_of_region(compute, region, project):
    """ Returns the name of the zones inside a region.
    """
    list_of_zones = []

    request = compute.zones().list(project=project)
    while request is not None:
        response = request.execute()

        for zone in response['items']:
            # Check if the zone is inside our region
            if region in zone['description']:
                list_of_zones.append(zone['description'])

        request = compute.zones().list_next(
            previous_request=request, previous_response=response)
    return list_of_zones

def list_instances(compute, project, zone):
    """ List Compute instances inside a zone.
    """
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None


def read_default_config():
    """ Returns default configuration in json from Google Cloud SDK
    """
    result = subprocess.Popen(
        ['gcloud', 'config', 'list', "--format='json'"], stdout=subprocess.PIPE)
    out = result.stdout.read()
    out_json = json.loads(out)
    return out_json


class GCPDriver(AbstractDriver):
    """
        Concrete implementation of the GCP cloud driver.
    """

    def __init__(self, cloud=None, conn=None, logger=None, config=None):
        self.logger = logger or makeLogger(__name__)
        self.conn = create_connection_from_config()
        self.remote_servers = []
        try:
            if not config:
                default_config = read_default_config()
            else:
                with open(config, "r") as f:
                    default_config = json.loads(f.read())
            self.logger.debug(
                "Using Default gcloud config with project: %s and region: %s",
                default_config['core']['project'],
                default_config['compute']['region'])
            self.region = default_config['compute']['region']
            self.project = default_config['core']['project']
        except Exception:
            self.logger.error("gcloud config file isn't valid")
            self.logger.info("Exiting")
            sys.exit(0)

    def sync(self):
        """ Downloads a fresh set of nodes from the API.
        """
        self.logger.debug("Synchronizing remote nodes")
        self.remote_servers = []
        self.zones = get_zones_of_region(self.conn, self.region, self.project)
        if self.zones is not None:
            for zone in self.zones:
                instances = list_instances(self.conn, self.project, zone)
                if instances is not None:
                    for instance in instances:
                        self.remote_servers.append(instance)
        self.logger.info("Fetched %s remote servers" %
                         len(self.remote_servers))

    def get_by_ip(self, ip):
        """ Retrieve an instance of Node by its IP.
        """
        for server in self.remote_servers:
            addresses = get_all_ips(server)
            if not addresses:
                self.logger.warning("No ip addresses found: %s", server)
            else:
                for addr in addresses:
                    if addr == ip:
                        return create_node_from_server(server)
        return None

    def stop(self, node):
        """ Stop a Node.
        """
        self.conn.instances().stop(
            project=self.project,
            zone=node.az,
            instance=node.name).execute()

    def start(self, node):
        """ Start a Node.
        """
        self.conn.instances().start(
            project=self.project,
            zone=node.az,
            instance=node.name).execute()

    def delete(self, node):
        """ Delete a Node permanently.
        """
        self.conn.instances().delete(
            project=self.project,
            zone=node.az,
            instance=node.name).execute()
