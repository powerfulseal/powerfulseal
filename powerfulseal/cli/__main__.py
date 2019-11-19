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
import coloredlogs
import textwrap
import sys
import os
import six

import powerfulseal.version
from powerfulseal.k8s.metrics_server_client import MetricsServerClient
from powerfulseal.policy.demo_runner import DemoRunner
from prometheus_client import start_http_server
from powerfulseal.metriccollectors import StdoutCollector, PrometheusCollector, DatadogCollector
from powerfulseal.policy.label_runner import LabelRunner
from powerfulseal.web.server import ServerState, start_server, ServerStateLogHandler
from ..node import NodeInventory
from ..node.inventory import read_inventory_file_to_dict
from ..clouddrivers import OpenStackDriver, AWSDriver, NoCloudDriver, AzureDriver, GCPDriver
from ..execute import RemoteExecutor
from ..k8s import K8sClient, K8sInventory
from .pscmd import PSCmd
from ..policy import PolicyRunner

KUBECONFIG_DEFAULT_PATH = "~/.kube/config"

def parse_kubeconfig(args):
    """
        if explicitly set, use the --kubeconfig value
        otherwise, check if KUBECONFIG is set
        if not, check if there is `~/.kube/config` available
        else try to build in-cluster config
    """
    logger = logging.getLogger(__name__)
    kube_config = None
    expanded_home_kube_config_path = os.path.expanduser(KUBECONFIG_DEFAULT_PATH)
    if args.kubeconfig:
        kube_config = args.kubeconfig
        logger.info("Creating kubernetes client with config %s from --kubeconfig flag", kube_config)
    elif os.environ.get("KUBECONFIG"):
        kube_config = os.path.expanduser(os.environ.get("KUBECONFIG"))
        logger.info("Creating kubernetes client with config %s from KUBECONFIG env var", kube_config)
    elif os.path.exists(expanded_home_kube_config_path):
        kube_config = expanded_home_kube_config_path
        logger.info("Creating kubernetes client with config %s (path found for backwards compatibility)", kube_config)
    else:
        logger.info("Creating kubernetes client with in-cluster config")
    return kube_config

def add_kubernetes_options(parser):
    # Kubernetes
    args_kubernetes = parser.add_argument_group('Kubernetes settings')
    args_kubernetes.add_argument(
        '--kubeconfig',
        help='Location of kube-config file',
        type=os.path.expanduser
    )
    args_kubernetes.add_argument(
        '--use-pod-delete-instead-of-ssh-kill',
        help='If set, will not require SSH (will delete pods instead)',
        default=False,
        action='store_true',
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
        '--override-ssh-host',
        help=(
            'If you\'d like to execute all commands on a different host '
            '(for example for minikube) you can override it here'
        )
    )
    args_ssh.add_argument(
        '--use-private-ip',
        default=False,
        action='store_true',
        help='Use the private IP of each node (vs public IP)',
    )
    ssh_options = args_ssh.add_mutually_exclusive_group()
    ssh_options.add_argument(
        '--ssh-path-to-private-key',
        default=os.environ.get("PS_PRIVATE_KEY"),
        help='Path to ssh private key',
    )
    ssh_options.add_argument(
        '--ssh-password',
        default=os.environ.get("PS_SSH_PASSWORD"),
        help='ssh password',
    )
    args_ssh.add_argument(
        '--ssh-kill-command',
        default=os.environ.get("PS_SSH_KILL_COMMAND", "sudo docker kill -s {signal} {container_id}"),
        help='The command to execute on remote host to kill the {container_id}',
    )

def add_inventory_options(parser):
    # Inventory
    args = parser.add_argument_group('Inventory settings')
    inventory_options = args.add_mutually_exclusive_group(required=True)
    inventory_options.add_argument('-i', '--inventory-file',
        default=os.environ.get("INVENTORY_FILE"),
        help=('the inventory file (in ini format) of groups '
              'of hosts to work with')
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
    cloud_options.add_argument('--azure',
        default=os.environ.get("AZURE_CLOUD"),
        action='store_true',
        help="use Azure cloud provider",
    )
    cloud_options.add_argument('--gcp',
        default=os.environ.get("GCP_CLOUD"),
        action='store_true',
        help="use GCP cloud provider",
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
    args.add_argument('--azure-resource-group-name',
        default=os.environ.get("AZURE_RESORUCE_GROUP_NAME"),
        help="optional name of the Azure vm cluster resource group. Used to determine azure-node-resource-group-name.",
    )
    args.add_argument('--azure-node-resource-group-name',
        default=os.environ.get("AZURE_NODE_RESORUCE_GROUP_NAME"),
        help="name of the Azure vm cluster node resource group",
    )
    args.add_argument('--gcp-config-file',
        default=os.environ.get("GCP_CONFIG_FILE"),
        help="name of the gcloud config file (in json) to use instead of the default one",
    )

def add_namespace_options(parser):
    args = parser.add_argument_group('Kubernetes options')
    args.add_argument('--kubernetes-namespace',
        default='default',
        help='Namespace to use for label and demo mode '
             '(set to blank for all namespaces)'
    )

def add_policy_options(parser):
    # Policy
    args = parser.add_argument_group('Policy settings')
    args.add_argument('--policy-file',
        default=os.environ.get("POLICY_FILE"),
        help='the policy file to run',
        required=True
    )

def add_run_options(parser):
    # policy settings
    run_args = parser.add_argument_group(
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

def add_metrics_options(parser):
    # metrics settings
    autonomous_args = parser.add_argument_group(
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
    metric_options.add_argument('--datadog-collector',
        default=os.environ.get("DATADOG_COLLECTOR"),
        action='store_true',
        help="send collected metrics to Datadog using DogStatsD"
    )

    args_prometheus = parser.add_argument_group('Prometheus settings')
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

def add_common_options(parser):
    add_kubernetes_options(parser)
    add_cloud_options(parser)
    add_inventory_options(parser)
    add_ssh_options(parser)


def check_valid_port(value):
    parsed = int(value)
    min_port = 0
    max_port = 65535
    if parsed < min_port or parsed > max_port:
        raise argparse.ArgumentTypeError("%s is an invalid port number" % value)
    return parsed


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
    parser.add_argument(
        '-V', '--version',
        action='version',
        version='%(prog)s {version}'.format(version=powerfulseal.version.__version__),
        help='Version.',
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
            'If you\'re reading this for the first time, you should probably '
            'start here. '
        ),
    )
    add_common_options(parser_interactive)


    ##########################################################################
    # AUTONOMOUS MODE
    ##########################################################################
    parser_autonomous = subparsers.add_parser('autonomous',
        help=(
            'This is the main mode of operation. It reads the policy file and executes it.'
        ),
    )
    add_common_options(parser_autonomous)
    add_policy_options(parser_autonomous)
    add_metrics_options(parser_autonomous)

    # web ui settings
    web_args = parser_autonomous.add_argument_group(
        title='Web UI settings'
    )
    web_args.add_argument(
        '--headless',
        help='Doesn\'t start the UI, just runs the policy',
        action='store_true'
    )
    web_args.add_argument(
        '--host',
        help='Specify host for the PowerfulSeal web server',
        default=os.environ.get('HOST', '127.0.0.1')
    )
    web_args.add_argument(
        '--port',
        help='Specify port for the PowerfulSeal web server',
        default=int(os.environ.get('PORT', '8080')),
        type=check_valid_port
    )
    web_args.add_argument(
        '--accept-proxy-headers',
        help='Set this flag for the webserver to accept X-Forwarded-* headers',
        action='store_true'
    )

    ##########################################################################
    # LABEL MODE
    ##########################################################################
    parser_label = subparsers.add_parser('label',
        help=(
            'Starts in label mode. '
            'It reads Kubernetes pods in a specified namespace, and checks '
            ' their \'seal/*\' labels to decide which ones to kill.'
            'There is no policy needed in this mode. '
            'To learn about supported labels, read more at '
            'https://github.com/bloomberg/powerfulseal/ '
        ),
    )
    add_common_options(parser_label)
    add_namespace_options(parser_label)
    add_run_options(parser_label)
    add_metrics_options(parser_label)

    ##########################################################################
    # DEMO MODE
    ##########################################################################
    parser_demo = subparsers.add_parser('demo',
        help=(
            'Starts in demo mode. '
            'It reads Kubernetes pods in specified namespaces, and reads '
            'metrics-server metrics to guess what\'s worth killing. '
        ),
    )
    add_common_options(parser_demo)
    add_namespace_options(parser_demo)
    add_run_options(parser_demo)
    add_metrics_options(parser_demo)

    demo_options = parser_demo.add_argument_group(
        title='metrics-server settings'
    )
    demo_options.add_argument('--metrics-server-path',
        help='Base path of metrics-server without trailing slash',
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

    if args.mode is None:
        return parse_args(['--help'])

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
    coloredlogs.install(logger=logger)

    my_verb = args.verbose
    logger.info("modules %s : verbosity %s : log level %s : handler level %s ", __name__, my_verb, logging.getLevelName(logger.getEffectiveLevel()), logging.getLevelName(log_level) )

    ##########################################################################
    # KUBERNETES
    ##########################################################################
    kube_config = parse_kubeconfig(args)
    k8s_client = K8sClient(kube_config=kube_config)
    k8s_inventory = K8sInventory(
        k8s_client=k8s_client,
        delete_pods=args.use_pod_delete_instead_of_ssh_kill
    )

    ##########################################################################
    # CLOUD DRIVER
    ##########################################################################
    if args.openstack:
        logger.info("Building OpenStack driver")
        driver = OpenStackDriver(
            cloud=args.openstack_cloud_name,
        )
    elif args.aws:
        logger.info("Building AWS driver")
        driver = AWSDriver()
    elif args.azure:
        logger.info("Building Azure driver")
        driver = AzureDriver(
            cluster_rg_name=args.azure_resource_group_name,
            cluster_node_rg_name=args.azure_node_resource_group_name,
        )
    elif args.gcp:
        logger.info("Building GCP driver")
        driver = GCPDriver(config=args.gcp_config_file)
    else:
        logger.info("No driver - some functionality disabled")
        driver = NoCloudDriver()

    ##########################################################################
    # INVENTORY
    ##########################################################################
    if args.inventory_file:
        logger.info("Reading inventory from %s", args.inventory_file)
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

    ##########################################################################
    # SSH EXECUTOR
    ##########################################################################
    if args.use_private_ip:
        logger.info("Using each node's private IP address")
    executor = RemoteExecutor(
        user=args.remote_user,
        ssh_allow_missing_host_keys=args.ssh_allow_missing_host_keys,
        ssh_path_to_private_key=args.ssh_path_to_private_key,
        override_host=args.override_ssh_host,
        ssh_password=args.ssh_password,
        use_private_ip=args.use_private_ip,
        ssh_kill_command=args.ssh_kill_command,
    )

    ##########################################################################
    # INTERACTIVE MODE
    ##########################################################################
    if args.mode == 'interactive':
        # create a command parser
        cmd = PSCmd(
            inventory=inventory,
            driver=driver,
            executor=executor,
            k8s_inventory=k8s_inventory,
        )
        logger.info("STARTING INTERACTIVE MODE")
        while True:
            try:
                cmd.cmdloop()
            except GeneratorExit:
                print("Exiting")
                sys.exit(0)
            except KeyboardInterrupt:
                print()
                print("Ctrl-c again to quit")
            try:
                six.moves.input()
            except KeyboardInterrupt:
                sys.exit(0)
        return

    ##########################################################################
    # METRICS
    ##########################################################################
    metric_collector = StdoutCollector()
    if args.prometheus_collector:
        flask_debug = os.environ.get("FLASK_DEBUG")
        flask_env = os.environ.get("FLASK_ENVIROMENT")
        if flask_debug is not None or (flask_env is not None and flask_env != "production"):
            logger.error("PROMETHEUS METRICS NOT SUPPORTED WHEN USING FLASK RELOAD. NOT STARTING THE SERVER")
        else:
            logger.info("Starting prometheus metrics server on %s", args.prometheus_port)
            start_http_server(args.prometheus_port, args.prometheus_host)
            metric_collector = PrometheusCollector()
    elif args.datadog_collector:
        logger.info("Starting datadog collector")
        metric_collector = DatadogCollector()
    else:
        logger.info("Using stdout metrics collector")

    ##########################################################################
    # AUTONOMOUS MODE
    ##########################################################################
    if args.mode == 'autonomous':

        # read and validate the policy
        policy = PolicyRunner.load_file(args.policy_file)
        if not PolicyRunner.is_policy_valid(policy):
            logger.info("Policy not valid. See log output above.")
            return os.exit(1)

        # run the metrics server if requested
        if not args.headless:
            # Create an instance of the singleton server state, ensuring all logs
            # for retrieval from the web interface
            state = ServerState(
                policy,
                inventory,
                k8s_inventory,
                driver,
                executor,
                args.host,
                args.port,
                args.policy_file,
                metric_collector=metric_collector,
            )
            server_log_handler = ServerStateLogHandler()
            server_log_handler.setLevel(log_level)
            logger.addHandler(server_log_handler)
            state.start_policy_runner()
            # start the server
            logger.info("Starting the UI server")
            start_server(args.host, args.port, args.accept_proxy_headers)
        else:
            logger.info("NOT starting the UI server")

            logger.info("STARTING AUTONOMOUS MODE")
            PolicyRunner.run(
                policy,
                inventory,
                k8s_inventory,
                driver,
                executor,
                metric_collector=metric_collector
            )

    ##########################################################################
    # LABEL MODE
    ##########################################################################
    elif args.mode == 'label':
        label_runner = LabelRunner(
            inventory,
            k8s_inventory,
            driver,
            executor,
            min_seconds_between_runs=args.min_seconds_between_runs,
            max_seconds_between_runs=args.max_seconds_between_runs,
            namespace=args.kubernetes_namespace,
            metric_collector=metric_collector,
        )
        logger.info("STARTING LABEL MODE")
        label_runner.run()

    ##########################################################################
    # DEMO MODE
    ##########################################################################
    elif args.mode == 'demo':
        aggressiveness = int(args.aggressiveness)
        if not 1 <= aggressiveness <= 5:
            print("Aggressiveness must be between 1 and 5 inclusive")
            os.exit(1)

        metrics_server_client = MetricsServerClient(args.metrics_server_path)
        demo_runner = DemoRunner(
            inventory,
            k8s_inventory,
            driver,
            executor,
            metrics_server_client,
            aggressiveness=aggressiveness,
            min_seconds_between_runs=args.min_seconds_between_runs,
            max_seconds_between_runs=args.max_seconds_between_runs,
            namespace=args.kubernetes_namespace,
            metric_collector=metric_collector,
        )
        logger.info("STARTING DEMO MODE")
        demo_runner.run()


def start():
    main(sys.argv[1:])


if __name__ == '__main__':
    start()
