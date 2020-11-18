import json
import os
import requests
import sys
from powerfulseal import makeLogger
from . import AbstractDriver
from ..node import Node, NodeState

from azure.common.client_factory import get_client_from_auth_file
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

def create_connection_from_config():
    """ Creates a new Azure api connection """
    resource_client = None
    compute_client = None
    network_client = None
    try:
        os.environ['AZURE_AUTH_LOCATION']
    except KeyError:
        try:
            subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']
            credentials = DefaultAzureCredential()
        except KeyError:
            sys.exit("No Azure Connection Defined")
        else:
           resource_client = ResourceManagementClient(credentials, subscription_id)
           compute_client = ComputeManagementClient(credentials, subscription_id)
           network_client = NetworkManagementClient(credentials, subscription_id)
    else:
        resource_client = get_client_from_auth_file(ResourceManagementClient)
        compute_client = get_client_from_auth_file(ComputeManagementClient)
        network_client = get_client_from_auth_file(NetworkManagementClient)

    return resource_client, compute_client, network_client

def server_state(compute_client, server):
    ret_state=NodeState.UNKNOWN
    try:
        tmp_rg="".join(server.id.split('/')[4])
        instance_view = compute_client.virtual_machines.instance_view(resource_group_name=tmp_rg, vm_name=server.name)
        status_code_operating = ",".join([s.code for s in instance_view.statuses]) or 'Unknown'
        if status_code_operating == 'ProvisioningState/succeeded,PowerState/running':
            ret_state=NodeState.UP
        elif status_code_operating != 'Unknown':
            ret_state=NodeState.DOWN
    except:
        """ignore"""

    return ret_state

def create_node_from_server(compute_client,server,int_ip, ext_ip):
    return Node(
        id=server.id,
        ip=int_ip,
        extIp=ext_ip or int_ip,
        az=server.location,
        name=server.name,
        state=server_state(compute_client,server)
    )

def get_auth_token():
    client_id = os.getenv('AZURE_CLIENT_ID')
    secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant = os.getenv('AZURE_TENANT_ID')

    creds = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": secret,
        "resource": "https://management.azure.com/",
        "tenant": tenant
    }
    if creds['client_id'] and creds['client_secret'] and creds['tenant']:
        res_json = json.loads(requests.post('https://login.microsoftonline.com/'+tenant+'/oauth2/token', data=creds).text)
        return res_json['access_token']
    return None

class AzureDriver(AbstractDriver):
    """
        Concrete implementation of the Azure cloud driver.
    """

    def __init__(self, cluster_rg_name=None, cluster_node_rg_name=None, cloud=None, conn=None, logger=None):
        self.logger = logger or makeLogger(__name__)
        self.resource_client, self.compute_client, self.network_client = create_connection_from_config()
        self.remote_servers = []
        self.cluster_rg = cluster_rg_name
        self.cluster_node_rg = cluster_node_rg_name
        self.ipconfig_cache = {}
        self.access_token = get_auth_token()

    def get_all_ips(self, instance, network_client):
        """ Returns the private and public ip addresses of an Azure instances
        """
        output = []
        for interface in instance.network_profile.network_interfaces:
            if_name = " ".join(interface.id.split('/')[-1:])
            rg = "".join(interface.id.split('/')[4])

            try:
                thing = self.ipconfig_cache.get(if_name)
                if thing is None:
                    thing = network_client.network_interfaces.get(
                        rg, if_name).ip_configurations
                    self.ipconfig_cache[if_name] = thing
                for x in thing:
                    private_ip = x.private_ip_address
                    public_ip = None
                    """print('\nifdata: ',rg,if_name,x.private_ip_address,x.public_ip_address)"""
                    """ Have to extract public IP from public IP class structure...if present """
                    if x.public_ip_address is not None:
                        public_ip_id = x.public_ip_address.id
                        public_ip_name = " ".join(public_ip_id.split('/')[-1:])
                        try:
                            public_ip_return = network_client.public_ip_addresses.get(
                                rg, public_ip_name)
                            public_ip = public_ip_return.ip_address
                        except:
                            """ Ignore the exception.  return no additional values """

                    temp_pair = (private_ip, public_ip)
                    output.append(temp_pair)

            except Exception:
                """ Ignore the exception.  return no additional values """

        return output

    def getResourceGroups(self):
        """ Find nodeResourceGroup for the cluster.
            This can be determined by finding the resource groups that are managed_by
            the cluater resource group ID
        """
        self.logger.debug("++ Azure cluster_rg: %s", self.cluster_rg)
        self.logger.debug("++ Azure cluster_node_rg: %s", self.cluster_node_rg)

        if self.cluster_node_rg is None:
            if self.cluster_rg is not None:
                """ get the nodeResouceGroup for the cluster ResourceGroup """
                crg = self.resource_client.resource_groups.get(self.cluster_rg)
                """ get resource groups managedBy the returned id e.g. crg.id == <>.managed_by """
                """ NOTE: azure python API resource selection filter does not appear to select correctly,
                So, query all resources and process here instead.
                """
                rgl = self.resource_client.resource_groups.list(None)
                for trg in rgl:
                    if trg.managed_by is not None:
                        if trg.managed_by.startswith(crg.id):
                            self.cluster_node_rg = trg.name
                            self.logger.info("++ Azure cluster_node_rg set to: %s", self.cluster_node_rg)
                            break
            else:
                """ Don't have the cluster resource group.
                    NOTE: it should be possible to determine it from the kubernetes cluster name.
                    however, the current (4/17/2019), python azure API doesn't support
                    querying aks by kubernetes cluster name.
                """
                self.logger.warning("Azure Cluster Resource Group is not specified.  Please specify as an argument.")


    def sync(self):
        """ Downloads a fresh set of nodes form the API.
        """
        self.logger.debug("Synchronizing remote nodes")
        """only get the resource group for the current cluster
        """
        self.getResourceGroups()
        self.remote_servers = []
        if self.cluster_node_rg is not None:
            self.remote_servers = list(self.compute_client.virtual_machines.list(self.cluster_node_rg))
            self.remote_servers.extend(self.get_scaleset_vms())
        else:
            self.logger.warning("No Azure cluster node resource group was found, the node list may be incorrect.")
            self.remote_servers = list(self.compute_client.virtual_machines.list_all())

        self.logger.info("Fetched %s remote servers" % len(self.remote_servers))

    def get_scaleset_vms(self):
        """ Get vms in a scaleset. This is used for AKS nodes.
        """
        self.logger.debug("Getting AKS nodes")
        vmss = self.compute_client.virtual_machine_scale_sets.list(self.cluster_rg)
        scalesetvms = []
        vms = []

        for scaleset in vmss:
            scalesetvms = self.compute_client.virtual_machine_scale_set_vms.list(self.cluster_rg, scaleset.name)

            for vm in scalesetvms:
                vms.append(vm)

        return vms


    def get_by_ip(self, ip):
        """ Retrieve an instance of Node by its IP.
        """
        for server in self.remote_servers:
            addresses = []
            if server.type == 'Microsoft.Compute/virtualMachines':
                addresses = self.get_all_ips(server, self.network_client)
            elif server.type == 'Microsoft.Compute/virtualMachineScaleSets/virtualMachines':
                addresses = self.get_vmss_ips(self.cluster_rg, server.name.split("_")[0])

            if not addresses:
                self.logger.warning("No ip addresses found: %s", server.__dict__)
            else:
                """ returns first node """
                for addr in addresses:
                    if addr[0] == ip or addr[1] == ip:
                        new_node=create_node_from_server(compute_client=self.compute_client, server=server, int_ip=addr[0], ext_ip=addr[1])
                        return new_node
        return None

    def get_vmss_ips(self, resource_group_name, virtual_machine_scale_set_name):
        if self.access_token == None:
            self.access_token = get_auth_token()
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

        ips = []
        res_json = {}
        if subscription_id and resource_group_name and virtual_machine_scale_set_name:
            url = 'https://management.azure.com/subscriptions/' + subscription_id + \
                '/resourceGroups/' + resource_group_name + \
                '/providers/microsoft.Compute/virtualMachineScaleSets/' + virtual_machine_scale_set_name + \
                '/networkInterfaces/?api-version=2018-10-01'

            headers = {
                "Authorization": "Bearer " + self.access_token,
                "Content-Type": "application/json"
            }
            res_json = json.loads(requests.get(url, headers=headers).text)
            self.logger.debug("Trying to get VMSS ips")

        for i in res_json['value']:
            ips.append((i['properties']['ipConfigurations'][0]['properties']['privateIPAddress'], None))
        return ips

    def stop(self, node):
        """ Stop a Node.
        """
        if 'vmss_' in node.name:
            name_split = node.id.split('/')
            rg_name = name_split[4]
            ss_name = name_split[8]
            node_id = name_split[-1]
            async_vm_start = self.compute_client.virtual_machine_scale_set_vms.power_off(rg_name, ss_name, node_id)
        else:
            async_vm_start = self.compute_client.virtual_machines.power_off(self.cluster_node_rg, node.name)
        async_vm_start.wait()

    def start(self, node):
        """ Start a Node.
        """
        if 'vmss_' in node.name:
            name_split = node.id.split('/')
            rg_name = name_split[4]
            ss_name = name_split[8]
            node_id = name_split[-1]
            async_vm_restart = self.compute_client.virtual_machine_scale_set_vms.start(rg_name, ss_name, node_id)
        else:
            async_vm_restart = self.compute_client.virtual_machines.start(self.cluster_node_rg, node.name)
        async_vm_restart.wait()

    def delete(self, node):
        """ Delete a Node permanently.
        """
        if 'vmss_' in node.name:
            name_split = node.id.split('/')
            rg_name = name_split[4]
            ss_name = name_split[8]
            node_id = name_split[-1]
            async_vm_delete = self.compute_client.virtual_machine_scale_set_vms.delete(rg_name, ss_name, node_id)
        else:
            async_vm_delete = self.compute_client.virtual_machines.delete(self.cluster_node_rg, node.name)
        async_vm_delete.wait()
