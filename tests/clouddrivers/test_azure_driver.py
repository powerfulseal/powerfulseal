import pytest
from mock import patch, MagicMock
from powerfulseal.clouddrivers import azure_driver
from powerfulseal.node import Node, NodeState

PRIVATE_IPS = ['198.168.1.1', '198.168.1.2', '198.168.1.3']
PUBLIC_IPS = ['31.31.31.31', '41.41.41.41']
INVALID_IP = '198.168.3.1'

class VMPublicIP():
    def __init__(self,rg,name,ip):
        self.id='/subscriptions/a32253aa-111111/resourceGroups/'+rg+'/providers/Microsoft.Network/publicIPAddresses/'+name
        self.rg=rg
        self.name=name
        self.ip_address=ip

class VMPublicIPs():
    def __init__(self,rg,name,ip):
        self.theIP = VMPublicIP(rg,"bogusIP2","0.0.0.0")
        if name is not None:
            self.theIP=VMPublicIP(rg,name,ip)

    def get(self,rg,ipname):
        if rg == self.theIP.rg and ipname == self.theIP.name:
            return self.theIP
        return VMPublicIP(rg,"bogusIP2","0.0.0.0")

class VMIP():
    def __init__(self,priv_ip, rg, pub_ip_name, pub_ip):
        self.private_ip_address=priv_ip
        self.public_ip_address=None
        if pub_ip_name is not None:
            self.public_ip_address=VMPublicIP(rg, pub_ip_name,pub_ip)

class VMIPConfig():
    def __init__(self,rg,ifname,priv_ip,pub_ip_name, pub_ip):
        self.ip_configurations=[VMIP(priv_ip, rg, pub_ip_name, pub_ip)]
        self.rg = rg
        self.name = ifname

class VMNetworkInterface():
    def __init__(self, rg, ifname, priv_ip, pub_ip_name, pub_ip):
        self.theif= VMIPConfig(rg, ifname, priv_ip, pub_ip_name, pub_ip)

    def get(self,rg, name):
        if rg== self.theif.rg and name == self.theif.name:
            return self.theif
        return  VMIPConfig("foo", "bar", "10.10.10.10`", "bogusIp", "20.20.20.20")

class VMNetworkClient():
    def __init__(self, rg, ifname, priv_ip, pub_ip_name, pub_ip):
        self.network_interfaces=VMNetworkInterface(rg, ifname, priv_ip, pub_ip_name, pub_ip)
        self.public_ip_addresses=VMPublicIPs(rg, pub_ip_name, pub_ip)

class VMNetID():
    def __init__(self,rg, ifname):
        self.id='/subscriptions/a32253aa-111111/resourceGroups/'+rg+'/providers/Microsoft.Network/networkInterfaces/'+ifname 

class VMNetworkProfile():
    def __init__(self, rg, ifname):
        self.network_interfaces=[VMNetID(rg, ifname)]

class VMServerStatus():
    def __init__(self,state):
        self.code = state

class  VMServerMachine():
    def __init__(self, id, state):
        self.id = id
        self.statuses = [ VMServerStatus('ProvisioningState/succeeded'),  VMServerStatus(state) ]

    def instance_view(self,resource_group_name,vm_name):
        return self

class VMCompute():
    def __init__(self,id, state):
        self.virtual_machines = VMServerMachine(id, state)

class VMInstance():
    def __init__(self, id, name, zone, state, rg, ifname, priv_ip, pub_ip_name, pub_ip):
        self.id = id
        self.network_profile=VMNetworkProfile(rg, ifname)
        self.location = zone
        self.name = name
        self.state = state
        self.network_stuff = VMNetworkClient(rg, ifname, priv_ip, pub_ip_name, pub_ip)
        self.compute_stuff = VMCompute(id, state)

   
@pytest.fixture
def vm_instances():
    return [
        VMInstance(id="/subscriptions/a32253aa-111111/resourceGroups/MC_test-rg-2_westus/providers/Microsoft.Compute/virtualMachines/aks-workers-67219403-0", name="aks-workers-67219403-0", zone="westus", state="PowerState/running", rg="MC_test-rg-2_westus", ifname="two",priv_ip="198.168.1.1", pub_ip_name="publicIp01",pub_ip="31.31.31.31"),
        VMInstance(id="/subscriptions/a32253aa-111111/resourceGroups/MC_test-rg-2_westus/providers/Microsoft.Compute/virtualMachines/aks-workers-67219403-1", name="aks-workers-67219403-1", zone="westus", state="PowerState/stopped", rg="MC_test-rg-2_westus", ifname="four",priv_ip="198.168.1.2", pub_ip_name="publicIp02", pub_ip="41.41.41.41"),
        VMInstance(id="/subscriptions/a32253aa-111111/resourceGroups/MC_test-rg-2_westus/providers/Microsoft.Compute/virtualMachines/aks-workers-67219403-2", name="aks-workers-67219403-2", zone="westus", state="UNKNOWN", rg="MC_test-rg-2_westus", ifname="six",priv_ip="198.168.1.3", pub_ip_name=None, pub_ip=None),
]


@patch('powerfulseal.clouddrivers.azure_driver.create_connection_from_config', return_value=(None, None, None))
def test_get_by_ip_private_ip_nodes(create_connection_from_config, vm_instances):
    driver = azure_driver.AzureDriver()
    driver.remote_servers = vm_instances
    node_index = 0
    driver.network_client = vm_instances[node_index].network_stuff
    driver.compute_client =  vm_instances[node_index].compute_stuff
    nodes = driver.get_by_ip(PRIVATE_IPS[node_index])
    assert vm_instances[node_index].id is nodes.id
    assert vm_instances[node_index].location is nodes.az
    assert vm_instances[node_index].network_stuff.network_interfaces.theif.ip_configurations[0].private_ip_address == nodes.ip

@patch('powerfulseal.clouddrivers.azure_driver.create_connection_from_config', return_value=(None, None, None))
def test_get_by_ip_public_ip_nodes(create_connection_from_config, vm_instances):
    driver = azure_driver.AzureDriver()
    driver.remote_servers = vm_instances
    node_index = 1
    driver.network_client = vm_instances[node_index].network_stuff
    nodes = driver.get_by_ip(PUBLIC_IPS[node_index])
    assert vm_instances[node_index].id is nodes.id
    assert vm_instances[node_index].location is nodes.az
    assert vm_instances[node_index].network_stuff.network_interfaces.theif.ip_configurations[0].public_ip_address.ip_address== nodes.extIp

@patch('powerfulseal.clouddrivers.azure_driver.create_connection_from_config', return_value=(None, None, None))
def test_get_by_ip_no_nodes(create_connection_from_config, vm_instances):
    driver = azure_driver.AzureDriver()
    driver.remote_servers = vm_instances
    driver.network_client = vm_instances[2].network_stuff
    nodes = driver.get_by_ip(INVALID_IP)
    assert nodes is None
