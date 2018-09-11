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
from ..node import NodeInventory
from ..node.inventory import read_inventory_file_to_dict
from ..clouddrivers import OpenStackDriver, AWSDriver, NoCloudDriver
from ..execute import RemoteExecutor
from ..k8s import K8sClient, K8sInventory
from .pscmd import PSCmd
from ..policy import PolicyRunner


def parse_args(args):
    prog = ArgumentParser(
        config_file_parser_class=YAMLConfigFileParser,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        default_config_files=['~/.config/seal', '~/.seal'],
        description=textwrap.dedent("""\
            PowerfulSeal
        """),
    )

    # General settings
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

    # Policy
    # If --validate-policy-file is set, the other arguments are not used
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
    policy_options.add_argument('--label',
        help='starts the seal in label mode',
        action='store_true',
    )
    policy_options.add_argument('--demo',
        help='starts the demo mode',
        action='store_true'
    )

    is_validate_policy_file_set = '--validate-policy-file' in args

    # Demo mode
    demo_options = prog.add_argument_group()
    demo_options.add_argument('--heapster-path',
        help='Base path of Heapster without trailing slash'
    )
    demo_options.add_argument('--aggressiveness',
        help='Aggressiveness of demo mode (default: 3)',
        default=3,
        type=int
    )

    # Arguments for both label and demo mode
    prog.add_argument('--namespace',
        default='default',
        help='Namespace to use for label and demo mode, defaults to the default '
             'namespace (set to blank for all namespaces)'
    )
    prog.add_argument('--min-seconds-between-runs',
        help='Minimum number of seconds between runs',
        default=0,
        type = int
    )
    prog.add_argument('--max-seconds-between-runs',
        help='Maximum number of seconds between runs',
        default=300,
        type = int
    )

    # Inventory
    inventory_options = prog.add_mutually_exclusive_group(required=not is_validate_policy_file_set)
    inventory_options.add_argument('-i', '--inventory-file',
        default=os.environ.get("INVENTORY_FILE"),
        help='the inventory file of group of hosts to test'
    )
    inventory_options.add_argument('--inventory-kubernetes',
        default=os.environ.get("INVENTORY_KUBERNETES"),
        help='will read all cluster nodes as inventory',
        action='store_true',
    )

    # SSH
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
    args_ssh.add_argument(
        '--ssh-path-to-private-key',
        default=os.environ.get("PS_PRIVATE_KEY"),
        help='Path to ssh private key',
    )

    # Cloud Driver
    cloud_options = prog.add_mutually_exclusive_group(required=not is_validate_policy_file_set)
    cloud_options.add_argument('--open-stack-cloud',
        default=os.environ.get("OPENSTACK_CLOUD"),
        action='store_true',
        help="use OpenStack cloud provider",
    )
    cloud_options.add_argument('--aws-cloud',
        default=os.environ.get("AWS_CLOUD"),
        action='store_true',
        help="use AWS cloud provider",
    )
    cloud_options.add_argument('--no-cloud',
        default=os.environ.get("NO_CLOUD"),
        action='store_true',
        help="don't use cloud provider",
    )
    prog.add_argument('--open-stack-cloud-name',
        default=os.environ.get("OPENSTACK_CLOUD_NAME"),
        help="the name of the open stack cloud from your config file to use (if using config file)",
    )

    # Metric Collector
    metric_options = prog.add_mutually_exclusive_group(required=False)
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

    args_prometheus = prog.add_argument_group('Prometheus settings')
    args_prometheus.add_argument(
        '--prometheus-host',
        default='127.0.0.1',
        help='Host to expose Prometheus metrics via the HTTP server when using the --prometheus-collector flag'
    )
    args_prometheus.add_argument(
        '--prometheus-port',
        default=8000,
        help='Port to expose Prometheus metrics via the HTTP server when using the --prometheus-collector flag',
        type=check_valid_port
    )

    # Kubernetes
    args_kubernetes = prog.add_argument_group('Kubernetes settings')
    args_kubernetes.add_argument(
        '--kube-config',
        default=None,
        help='Location of kube-config file',
    )

    return prog.parse_args(args=args)


def main(argv):
    """
        The main function to invoke the powerfulseal cli
    """
    args = parse_args(args=argv)

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
        PolicyRunner.validate_file(args.validate_policy_file)
        print("All good, captain")
    elif args.run_policy_file:
        policy = PolicyRunner.validate_file(args.run_policy_file)
        PolicyRunner.run(policy, inventory, k8s_inventory, driver, executor,
                         metric_collector=metric_collector)


def start():
    main(sys.argv[1:])


if __name__ == '__main__':
    start()
