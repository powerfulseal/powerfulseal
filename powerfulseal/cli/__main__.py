
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


import argparse
from configargparse import ArgumentParser, YAMLConfigFileParser
import logging
import textwrap
import sys
import os

from ..node import NodeInventory
from ..node.inventory import read_inventory_file_to_dict
from ..clouddrivers import OpenStackDriver
from ..execute import RemoteExecutor
from ..k8s import K8sClient, K8sInventory
from .pscmd import PSCmd
from ..policy import PolicyRunner

def main(argv):
    """
        The main function to invoke the powerfulseal cli
    """

    # Describe our configuration.
    prog = ArgumentParser(
        config_file_parser_class=YAMLConfigFileParser,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        default_config_files=['~/.config/seal', '~/.seal'],
        description=textwrap.dedent("""\
            PowerfulSeal
        """),
    )

    # general settings
    prog.add_argument(
        '-c', '--config',
        is_config_file=True,
        env_var="CONFIG",
        help='Config file path',
    )
    prog.add_argument('-v', '--verbose',
        action='count',
        help='Verbose logging.'
    )

    # inventory related config
    inventory_options = prog.add_mutually_exclusive_group(required=True)
    inventory_options.add_argument('-i', '--inventory-file',
        default=os.environ.get("INVENTORY_FILE"),
        help='the inventory file of group of hosts to test'
    )
    inventory_options.add_argument('--inventory-kubernetes',
        default=os.environ.get("INVENTORY_KUBERNETES"),
        help='will read all cluster nodes as inventory',
        action='store_true',
    )

    # ssh related options
    args_ssh = prog.add_argument_group('SSH settings')
    args_ssh.add_argument(
        '--remote-user',
        default=os.environ.get("PS_REMOTE_USER", "cloud-user"),
        help="the of the user for the ssh connections",
    )
    args_ssh.add_argument(
        '--ssh-allow-missing-host-keys',
        default=False,
        action='store_true',
        help='Allow connection to hosts not present in known_hosts',
    )

    # cloud driver related config
    cloud_options = prog.add_mutually_exclusive_group(required=False)
    cloud_options.add_argument('--open-stack-cloud',
        default=os.environ.get("OPENSTACK_CLOUD"),
        help="the name of the open stack cloud from your config file to use",
    )

    # KUBERNETES CONFIG
    args_kubernetes = prog.add_argument_group('Kubernetes settings')
    args_kubernetes.add_argument(
        '--kube-config',
        default=None,
        help='Location of kube-config file',
    )

    # policy-related settings
    policy_options = prog.add_mutually_exclusive_group(required=True)
    policy_options.add_argument('--validate-policy-file',
        help='reads the policy file, validates the schema, returns'
    )
    policy_options.add_argument('--run-policy-file',
        default=os.environ.get("POLICY_FILE"),
        help='location of the policy file to read',
    )
    policy_options.add_argument('--interactive',
        help='will start the seal in interactive mode',
        action='store_true',
    )

    args = prog.parse_args(args=argv)

    # Configure logging
    if not args.verbose:
        log_level = logging.ERROR
    elif args.verbose == 1:
        log_level = logging.WARNING
    elif args.verbose == 2:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    logging.basicConfig(
        stream=sys.stdout,
        level=log_level
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # build cloud inventory
    logger.debug("Fetching the remote nodes")
    driver = OpenStackDriver(
        cloud=args.open_stack_cloud,
    )

    # build a k8s client
    kube_config = args.kube_config
    logger.debug("Creating kubernetes client with config %d", kube_config)
    k8s_client = K8sClient(kube_config=kube_config)
    k8s_inventory = K8sInventory(k8s_client=k8s_client)

    # read the local inventory
    logger.debug("Fetching the inventory")
    if args.inventory_file:
        groups_to_restrict_to = read_inventory_file_to_dict(
            args.inventory_file
        )
    else:
        logger.info("Attempting to read the inventory from kubernetes")
        groups_to_restrict_to = k8s_client.get_nodes_groups()

    logger.debug("Restricting inventory to %s" % groups_to_restrict_to)

    inventory = NodeInventory(
        driver=driver,
        restrict_to_groups=groups_to_restrict_to,
    )
    inventory.sync()

    # create an executor
    executor = RemoteExecutor(
        user=args.remote_user,
        ssh_allow_missing_host_keys=args.ssh_allow_missing_host_keys,
    )

    if args.interactive:
        # create a command parser
        cmd = PSCmd(
            inventory=inventory,
            driver=driver,
            executor=executor,
            k8s_inventory=k8s_inventory,
        )
        while True:
            try:
                cmd.cmdloop()
            except KeyboardInterrupt:
                print()
                print("Ctrl-c again to quit")
            try:
                input()
            except KeyboardInterrupt:
                sys.exit(0)
    elif args.validate_policy_file:
        PolicyRunner.validate_file(args.validate_policy_file)
        print("All good, captain")
    elif args.run_policy_file:
        policy = PolicyRunner.validate_file(args.run_policy_file)
        PolicyRunner.run(policy, inventory, k8s_inventory, driver, executor)


def start():
    main(sys.argv[1:])

if __name__ == '__main__':
    start()
