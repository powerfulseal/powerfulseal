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

from __future__ import print_function
import argparse

import yaml
from configargparse import ArgumentParser, YAMLConfigFileParser
import logging
import textwrap
import sys
import os

from powerfulseal.k8s.heapster_client import HeapsterClient
from powerfulseal.policy.demo_runner import DemoRunner
from prometheus_client import start_http_server
from powerfulseal.metriccollectors import StdoutCollector, PrometheusCollector
from powerfulseal.policy.label_runner import LabelRunner
from powerfulseal.web.server import ServerState, start_server, ServerStateLogHandler
from ..node import NodeInventory
from ..node.inventory import read_inventory_file_to_dict
from ..clouddrivers import OpenStackDriver, AWSDriver, NoCloudDriver
from ..execute import RemoteExecutor
from ..k8s import K8sClient, K8sInventory
from .pscmd import PSCmd
from ..policy import PolicyRunner


def add_kubernetes_options(parser):
    # Kubernetes
    args_kubernetes = parser.add_argument_group('Kubernetes settings')
    args_kubernetes.add_argument(
        '--kubeconfig',
        help='Location of kube-config file',
        required=True,
    )

def add_ssh_options(parser):
    # SSH
    args_ssh = parser.add_argument_group('SSH settings')
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
    args_ssh.add_argument(
        '--ssh-path-to-private-key',
        default=os.environ.get("PS_PRIVATE_KEY"),
        help='Path to ssh private key',
    )

def add_inventory_options(parser):
    # Inventory
    args = parser.add_argument_group('Inventory settings')
    inventory_options = args.add_mutually_exclusive_group(required=True)
    inventory_options.add_argument('-i', '--inventory-file',
        default=os.environ.get("INVENTORY_FILE"),
        help='the inventory file of groups of hosts to work with'
    )
    inventory_options.add_argument('--inventory-kubernetes',
        default=os.environ.get("INVENTORY_KUBERNETES"),
        help='reads all kubernetes cluster nodes as inventory',
        action='store_true',
    )

def add_cloud_options(parser):
    # Cloud Driver
    args = parser.add_argument_group('Cloud settings')
    cloud_options = args.add_mutually_exclusive_group(required=True)
    cloud_options.add_argument('--openstack',
        default=os.environ.get("OPENSTACK_CLOUD"),
        action='store_true',
        help="use OpenStack cloud provider",
    )
    cloud_options.add_argument('--aws',
        default=os.environ.get("AWS_CLOUD"),
        action='store_true',
        help="use AWS cloud provider",
    )
    cloud_options.add_argument('--no-cloud',
        default=os.environ.get("NO_CLOUD"),
        action='store_true',
        help="don't use cloud provider",
    )
    # other options
    args.add_argument('--openstack-cloud-name',
        default=os.environ.get("OPENSTACK_CLOUD_NAME"),
        help="optional name of the open stack cloud from your config file to use",
    )

def add_namespace_options(parser):
    args = parser.add_argument_group('Kubernetes options')
    args.add_argument('--kubernetes-namespace',
        default='default',
        help='Namespace to use for label and demo mode, defaults to the default '
             'namespace (set to blank for all namespaces)'
    )

def add_policy_options(parser):
    # Policy
    args = parser.add_argument_group('Policy settings')
    args.add_argument('--policy-file',
        default=os.environ.get("POLICY_FILE"),
        help='the policy file to run'
    )



def parse_args(args):
    parser = ArgumentParser(
        config_file_parser_class=YAMLConfigFileParser,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        default_config_files=['~/.config/seal', '~/.seal'],
        description=textwrap.dedent("""\
            PowerfulSeal
            The Chaos Engineering tool for Kubernetes

        """),
    )

    # General settings
    parser.add_argument(
        '-c', '--config',
        is_config_file=True,
        env_var="CONFIG",
        help='Config file path',
    )
    parser.add_argument('-v', '--verbose',
        action='count',
        help='Verbose logging.'
    )
    # subparsers
    subparsers = parser.add_subparsers(
        title='MODES OF OPERATION',
        description=(
            'Pick one of the following options to start the Seal in the '
            'specified mode. Learn more at '
            'https://github.com/bloomberg/powerfulseal#introduction'
        ),
        dest='mode'
    )

    ##########################################################################
    # INTERACTIVE MODE
    ##########################################################################
    parser_interactive = subparsers.add_parser('interactive',
        help=(
            'Starts an interactive CLI, which allows to manually issue '
            'commands on pods and nodes and provides a sweet autocomplete. '
            'It requires access to Kubernetes, SSH access to execute kill '
            'commands on the hosts, and optionally a cloud driver to read '
            'metadata about nodes, and modify their state. '
            'If you\'re reading this for the first time, you should probably '
            'start here. '
            'This is a DAEMONLESS mode of operation.'
        ),
    )
    add_kubernetes_options(parser_interactive)
    add_cloud_options(parser_interactive)
    add_inventory_options(parser_interactive)
    add_ssh_options(parser_interactive)


    ##########################################################################
    # AUTONOMOUS MODE
    ##########################################################################
    parser_autonomous = subparsers.add_parser('autonomous',
        help=(
            'Starts in autonomous mode. '
            'This is the main mode of operation. The Seal reads the policy '
            'file and executes it indefinitely. '
            'It works on nodes and pods. '
            'It requires access to Kubernetes, SSH access to execute kill '
            'commands on the hosts, and optionally a cloud driver to read '
            'metadata about nodes, and modify their state. '
            'This is a DAEMONLESS mode of operation.'
        ),
    )
    add_policy_options(parser_autonomous)
    add_kubernetes_options(parser_autonomous)
    add_cloud_options(parser_autonomous)
    add_inventory_options(parser_autonomous)
    add_ssh_options(parser_autonomous)

    # policy settings
    run_args = parser_autonomous.add_argument_group(
        title='Policy settings'
    )
    run_args.add_argument('--min-seconds-between-runs',
        help='Minimum number of seconds between runs',
        default=0,
        type=int
    )
    run_args.add_argument('--max-seconds-between-runs',
        help='Maximum number of seconds between runs',
        default=300,
        type=int
    )

    # web ui settings
    web_args = parser_autonomous.add_argument_group(
        title='Web UI settings'
    )
    web_args.add_argument(
        '--disable-server',
        help='Start PowerfulSeal without the UI',
        action='store_true'
    )
    web_args.add_argument(
        '--host',
        help='Specify host for the PowerfulSeal web server',
        default='127.0.0.1'
    )
    web_args.add_argument(
        '--port',
        help='Specify port for the PowerfulSeal web server',
        default='8080'
    )

    # metrics settings
    autonomous_args = parser_autonomous.add_argument_group(
        title='Metrics settings'
    )
    metric_options = autonomous_args.add_mutually_exclusive_group(required=False)
    metric_options.add_argument('--stdout-collector',
        default=os.environ.get("STDOUT_COLLECTOR"),
        action='store_true',
        help="print metrics collected to stdout"
    )
    metric_options.add_argument('--prometheus-collector',
        default=os.environ.get("PROMETHEUS_COLLECTOR"),
        action='store_true',
        help="store metrics in Prometheus and expose metrics over a HTTP server"
    )

    def check_valid_port(value):
        parsed = int(value)
        min_port = 0
        max_port = 65535
        if parsed < min_port or parsed > max_port:
            raise argparse.ArgumentTypeError("%s is an invalid port number" % value)
        return parsed

    args_prometheus = parser_autonomous.add_argument_group('Prometheus settings')
    args_prometheus.add_argument(
        '--prometheus-host',
        default='127.0.0.1',
        help=(
            'Host to expose Prometheus metrics via the HTTP server when using '
            'the --prometheus-collector flag'
        ),
    )
    args_prometheus.add_argument(
        '--prometheus-port',
        default=8081,
        help=(
            'Port to expose Prometheus metrics via the HTTP server '
            'when using the --prometheus-collector flag'
        ),
        type=check_valid_port
    )


    ##########################################################################
    # LABEL MODE
    ##########################################################################
    parser_label = subparsers.add_parser('label',
        help=(
            'Starts in label mode. '
            'It reads Kubernetes pods in a specified namespace, and checks '
            ' their \'seal/*\' labels to decide which ones to kill.'
            'It requires access to Kubernetes. '
            'There is no policy needed in this mode. '
            'To learn about supported labels, read more at '
            'https://github.com/bloomberg/powerfulseal/ '
            'This is a DAEMONLESS mode of operation. '
        ),
    )
    add_kubernetes_options(parser_label)
    add_namespace_options(parser_label)

    ##########################################################################
    # DEMO MODE
    ##########################################################################
    parser_demo = subparsers.add_parser('demo',
        help=(
            'Starts in demo mode. '
            'It reads Kubernetes pods in specified namespaces, and reads '
            'HEAPSTER metrics to guess what\'s worth killing. '
            'It requires access to Kubernetes, SSH access to execute kill '
            'commands on the hosts. There is no policy needed in this mode. '
            'This is a DAEMONLESS mode of operation. '
        ),
    )
    add_kubernetes_options(parser_demo)
    add_namespace_options(parser_demo)

    demo_options = parser_demo.add_argument_group(
        title='Heapster settings'
    )
    demo_options.add_argument('--heapster-path',
        help='Base path of Heapster without trailing slash',
        required=True
    )
    demo_options.add_argument('--aggressiveness',
        help='Aggressiveness of demo mode (default: 3)',
        default=3,
        type=int
    )

    ##########################################################################
    # VALIDATE POLICY MODE
    ##########################################################################
    parser_validate_policy = subparsers.add_parser('validate',
        help=(
            'Validates any file against the policy schema, returns.'
            'You can use this to check that your policy is correct, '
            'before using it in autonomous mode.'
        )
    )
    add_policy_options(parser_validate_policy)

    return parser.parse_args(args=args)


def main(argv):
    """
        The main function to invoke the powerfulseal cli
    """
    args = parse_args(args=argv)

    ##########################################################################
    # VALIDATE POLICY MODE
    ##########################################################################
    if args.mode == 'validate':
        policy = PolicyRunner.load_file(args.policy_file)
        if PolicyRunner.is_policy_valid(policy):
            return print('OK')
        print("Policy not valid. See log output above.")
        return os.exit(1)

    ##########################################################################
    # LOGGING
    ##########################################################################
    # Ensure the logger config propagates from the root module of this package
    logger = logging.getLogger(__name__.split('.')[0])

    # The default level should be set to logging.DEBUG to ensure that the stdout
    # stream handler can filter to the user-specified verbosity level while the
    # server logging handler can receive all logs
    logger.setLevel(logging.DEBUG)

    # Configure logging for stdout
    if not args.verbose:
        log_level = logging.ERROR
    elif args.verbose == 1:
        log_level = logging.WARNING
    elif args.verbose == 2:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(log_level)
    logger.addHandler(stdout_handler)

    # build cloud provider driver
    logger.debug("Building the driver")
    if args.open_stack_cloud:
        logger.info("Building OpenStack driver")
        driver = OpenStackDriver(
            cloud=args.open_stack_cloud_name,
        )
    elif args.aws_cloud:
        logger.info("Building AWS driver")
        driver = AWSDriver()
    else:
        logger.info("No driver - some functionality disabled")
        driver = NoCloudDriver()

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
        ssh_path_to_private_key=args.ssh_path_to_private_key,
    )

    # create the collector which defaults to StdoutCollector()
    metric_collector = StdoutCollector()
    if args.prometheus_collector:
        if not args.prometheus_host:
            raise argparse.ArgumentTypeError("The Prometheus host must be specified with --prometheus-host")
        if not args.prometheus_port:
            raise argparse.ArgumentTypeError("The Prometheus port must be specified with --prometheus-port")
        start_http_server(args.prometheus_port, args.prometheus_host)
        metric_collector = PrometheusCollector()

    if args.server:
        # If the policy file already exists, then it must be valid. Otherwise,
        # create the policy file and write a default, empty policy to it.
        try:
            if not (os.path.exists(args.run_policy_file) and os.path.isfile(args.run_policy_file)):
                # Create a new policy file
                with open(args.run_policy_file, "w") as f:
                    policy = PolicyRunner.DEFAULT_POLICY
                    f.write(yaml.dump(policy, default_flow_style=False))
            else:
                policy = PolicyRunner.load_file(args.run_policy_file)
                if not PolicyRunner.is_policy_valid(policy):
                    print("Policy file exists but is not valid. Exiting.")
                    sys.exit(-1)
        except IOError:
            print("Unable to perform file operations. Exiting.")
            sys.exit(-1)

        # Create an instance of the singleton server state, ensuring all logs
        # for retrieval from the web interface
        ServerState(policy, inventory, k8s_inventory, driver, executor,
                    args.server_host, args.server_port, args.run_policy_file)
        server_log_handler = ServerStateLogHandler()
        server_log_handler.setLevel(logging.DEBUG)
        logger.addHandler(server_log_handler)
        start_server(args.server_host, int(args.server_port))
    elif args.interactive:
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
    elif args.demo:
        aggressiveness = int(args.aggressiveness)
        if not 1 <= aggressiveness <= 5:
            print("Aggressiveness must be between 1 and 5 inclusive")
            exit()

        heapster_client = HeapsterClient(args.heapster_path)
        demo_runner = DemoRunner(inventory, k8s_inventory, driver, executor,
                                 heapster_client, aggressiveness=aggressiveness,
                                 min_seconds_between_runs=int(args.min_seconds_between_runs),
                                 max_seconds_between_runs=int(args.max_seconds_between_runs),
                                 namespace=args.namespace)
        demo_runner.run()
    elif args.label:
        label_runner = LabelRunner(inventory, k8s_inventory, driver, executor,
                                   min_seconds_between_runs=int(args.min_seconds_between_runs),
                                   max_seconds_between_runs=int(args.max_seconds_between_runs),
                                   namespace=args.namespace)
        label_runner.run()
    elif args.validate_policy_file:
        policy = PolicyRunner.load_file(args.validate_policy_file)
        if PolicyRunner.is_policy_valid(policy):
            logger.info("All good, captain")
        else:
            logger.error("Policy not valid. See log output above.")
    elif args.run_policy_file:
        policy = PolicyRunner.load_file(args.run_policy_file)
        if not PolicyRunner.is_policy_valid(policy):
            logger.error("Policy not valid. See log output above.")
        PolicyRunner.run(policy, inventory, k8s_inventory, driver, executor,
                         metric_collector=metric_collector)


def start():
    main(sys.argv[1:])


if __name__ == '__main__':
    start()
