
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

import cmd
import shlex
from termcolor import colored, cprint
import sys

try:
    import readline
    readline.set_completer_delims(" ,")
except:
    pass

from ..execute import (
    SSHExecutor,
)

DEFAULT_COLOR_KEYWORDS = {
    "UP": "green",
    "DOWN": "red",
    "node": "blue",
    "pod": "blue",
    "host_ip": "yellow",
    "ip": "yellow",
    "extIp": "yellow",
    "Running": "green",
    "Succeeded": "green",
    "Pending": "grey",
    "Failed": "red",
    "Unknown": "red",
    "CrashLoopBackOff": "red",
    "error": "red",
    "Error": "red",
    "namespace": "blue"
}
# couple of helpers
def colour_output(output, extras=None):
    if extras is not None:
        pattern = extras.copy()
        pattern.update(DEFAULT_COLOR_KEYWORDS)
    else:
        pattern = DEFAULT_COLOR_KEYWORDS
    for word, colour in pattern.items():
        output = output.replace(
            word+'=', colored(word, colour)+'=').replace('='+word, '='+colored(word, colour))
    return output

def filter_text_insensitive(collection, item=None):
    return [
        element
        for element in collection
        if item is None or element.lower().startswith(item.lower())
    ]

class Command():
    def __init__(self, line):
        self.line = line
        self.args = shlex.split(line)
        self.finished = line and (line[-1] == " ")

    def get(self, index, default=None):
        if index < 0 or index >= len(self.args):
            return default
        return self.args[index]

    def __len__(self):
        return len(self.args)


class PSCmd(cmd.Cmd):
    """
        PowerfulSeal cli base class.
    """

    def __init__(self, inventory, driver, executor, k8s_inventory):
        cmd.Cmd.__init__(self)
        self.inventory = inventory
        self.driver = driver
        self.prompt = "(seal) $ "
        self.executor = executor
        self.k8s_inventory = k8s_inventory

    def completedefault(self, text, line, begidx, endidx):
        suggestions = []
        text_lower = text.lower()
        try:
            # try to match AZ
            for az in self.inventory.get_azs():
                if text_lower in az.lower():
                    suggestions.append(str(az))
            # try to match group name
            for group in self.inventory.get_groups():
                if text_lower in group.lower():
                    suggestions.append(str(group))
            # try to match name, id, state, ip
            for node in self.inventory.find_nodes():
                for attr in ["ip", "id", "state", "name", "no"]:
                    val = str(getattr(node, attr))
                    if text_lower in val.lower():
                        suggestions.append(val)
            # extras
            for extra in ("all",):
                if extra.lower().startswith(text.lower()):
                    suggestions.append(extra)
        except Exception as e:
            # sadly, if an exception is thrown here, it's just
            # silently swallowed...
            print(e)

        return suggestions

    def find_nodes(self, query):
        nodes = list(self.inventory.find_nodes(query))
        if not nodes:
            print(colored("No matching hosts", "yellow"))
        return nodes

    ###########################################################################
    # CLI control
    ###########################################################################
    def do_exit(self, line):
        "Exit CLI"
        raise GeneratorExit

    ###########################################################################
    # NODE (MACHINE) RELATED FUNCTIONALITY
    ###########################################################################

    def do_nodes(self, line):
        """
        Prints the nodes about a particular node

        Syntax:
            nodes [<subset>]
        """
        cmd = Command(line)
        query = cmd.get(0)
        if query:
            extras = {query: "blue"}
        else:
            extras = {}
        for node in self.find_nodes(query):
            print(colour_output(str(node), extras))

    def do_sync(self, line):
        """
        Synchronises the state with the remote API
        """
        self.inventory.sync()
        self.do_nodes("")

    def do_zones(self, line):
        """
        Prints availability zones
        """
        for az in self.inventory.get_azs():
            print(az)

    def do_groups(self, line):
        """
        Prints the groups
        """
        for group in self.inventory.get_groups():
            print(group)

    def do_start(self, line):
        """
        Brings up a subset of machines
        """
        cmd = Command(line)
        for node in self.find_nodes(cmd.get(0)):
            print("Starting %s" % (node))
            try:
                self.driver.start(node)
            except Exception as e:
                print(e)

    def do_stop(self, line):
        """
        Brings down a subset of machines
        """
        cmd = Command(line)
        for node in self.find_nodes(cmd.get(0)):
            print("Stopping %s" % (node))
            try:
                self.driver.stop(node)
            except Exception as e:
                print(e)

    def do_delete(self, line):
        """
        PERMANENTLY DELETES A NODE

        Syntax:
            delete <subset>
        """
        deleted = 0
        cmd = Command(line)
        if cmd.get(0) is None:
            return print("Can't delete all machines at once. It's for your own good")
        for node in self.find_nodes(cmd.get(0)):
            print("About to PERMANENTLY DELETE THIS NODE: \n{node}".format(
                node=colour_output(str(node))
            ))
            answer = None
            while answer not in ("yes", "no"):
                sys.stdout.write("Proceed ? (yes|no): ")
                answer = input()
            if answer == "yes":
                print("Deleting")
                self.driver.delete(node)
                deleted += 1
            else:
                print("Skipping")
        print("Deleted {num} nodes".format(num=deleted))


    ###########################################################################
    # EXECUTION ON SSH RELATED FUNCTIONALITY
    ###########################################################################

    def execute(self, command, nodes):
        """
        Executes a line in shell on specified boxes
        """
        try:
            for node in nodes:
                for key, value in self.executor.execute(
                    command, nodes=[node]
                ).items():
                    if value["ret_code"] > 0:
                        print(colored("-" * 80, "red"))
                        print(colored(key, "red"))
                        print(colored(value.get("stdout", ""), "red"))
                        print(colored(value.get("stderr", ""), "red"))
                        print(colored(value.get("error", ""), "red"))
                    else:
                        print(colored("-" * 80, "green"))
                        print(colored(key, "green"))
                        print(colored(value.get("stdout", ""), "white"))
                        if value.get("stderr"):
                            print(colored(value.get("stderr", ""), "red"))
        except KeyboardInterrupt:
            print(colored("-" * 80, "red"))
            print(colored("Interrupted by user", "red"))

    def do_exec(self, line, prefix=None):
        """
        Executes a line in shell on specified boxes

        Syntax:
            exec <subset> "command -to 'execute'"
        """
        cmd = Command(line)
        nodes = self.find_nodes(cmd.get(0))
        command = " ".join(cmd.args[1:])
        if prefix is not None:
            command = prefix + " " + command
        self.execute(command, nodes)

    def do_sudo(self, line, postfix=None):
        """
        Executes a line in shell on specified boxes with sudo

        Syntax:
            sudo <subset> "command -to 'execute'"
        """
        prefix = "sudo"
        if postfix is not None:
            prefix = prefix + " " + postfix
        self.do_exec(line, prefix=prefix)

    def do_kubectl(self, line):
        """
        Executes a command on kubectl

        Syntax:
            kubectl <subset> "command -to 'execute'"
        """
        self.do_exec(line, prefix="kubectl")

    def do_etcdctl(self, line):
        """
        Uses etcdctl to query and control etcd on a remote machine

        Syntax:
            etcdctl <subset> "command -to 'execute'"
        """
        self.do_exec(line, prefix="etcdctl")

    def do_docker(self, line):
        """
        Executes sudo docker [args, like -a]

        Syntax:
            docker <subset> [args, like -a]
        """
        self.do_sudo(line, postfix="docker")


    ###########################################################################
    # KUBERNETES RELATED FUNCTIONALITY
    ###########################################################################

    def do_namespaces(self, line):
        """
            Prints all the namespaces available
        """
        for namespace in self.k8s_inventory.find_namespaces():
            print(namespace)

    def complete_deployments(self, text, line, begidx, endidx):
        """
            Auto-complete for k8s deployments
        """
        return filter_text_insensitive(self.k8s_inventory.find_namespaces(), text)

    def do_deployments(self, line):
        """
        List deployments
        Syntax:
            deployments [namespace=default]
        """
        cmd = Command(line)
        namespace = cmd.get(0)
        for deploy in self.k8s_inventory.find_deployments(
            namespace=namespace,
        ):
            print(deploy)

    def complete_pods(self, text, line, begidx, endidx):
        """
            Auto-complete for k8s pods
        """
        cmd = Command(line)
        namespace = cmd.get(1)
        if len(cmd) == 1 or (len(cmd) == 2 and not cmd.finished):
            return filter_text_insensitive(self.k8s_inventory.find_namespaces(), namespace)
        return []

    def do_pods(self, line):
        """
        List pods
        Syntax:
            pods namespace [selector]
        Selector is in the kubernetes native form: app=something,ver=1
        """
        cmd = Command(line)
        namespace = cmd.get(0)
        selector = cmd.get(1)
        for pod in self.k8s_inventory.find_pods(
            namespace=namespace,
            selector=selector
        ):
            print(colour_output(str(pod)))

    def complete_pods_for_deployment(self, text, line, begidx, endidx):
        """
            Auto-complete for k8s pods for deployment
        """
        cmd = Command(line)
        namespace = cmd.get(1)
        if len(cmd) == 1 or (len(cmd) == 2 and not cmd.finished):
            return filter_text_insensitive(self.k8s_inventory.find_namespaces(), namespace)
        else:
            op = cmd.get(2)
            return filter_text_insensitive(self.k8s_inventory.find_deployments(namespace), op)

    def do_pods_for_deployment(self, line):
        """
        List pods for a deployment
        Syntax:
            pods_for_deployment namespace deployment-name
        """
        cmd = Command(line)
        namespace = cmd.get(0)
        deployment_name = cmd.get(1)
        for pod in self.k8s_inventory.find_pods(
            namespace=namespace,
            deployment_name=deployment_name,
        ):
            print(colour_output(str(pod)))

    def do_cached_pods(self, line):
        """
        List the last set of pods loaded.
        Useful, when you want to kill a pod
        Syntax:
            cached_pods
        """
        pods = self.k8s_inventory.last_pods
        if not pods:
            return print("No pods loaded. Use `pods` to load a set to choose from")
        for pod in pods:
            print(colour_output(str(pod)))

    def complete_kill(self, text, line, begidx, endidx):
        """
            Auto-complete for k8s pods killing
        """
        # TODO
        return []

    def do_kill(self, line):
        """
        Kill a pod
        Syntax:
            kill pod-number
        To show the pod numbers, run cached_pods.
        Executes `sudo docker kill <container ID> for each container in the pod`
        """
        cmd = Command(line)
        pod_num = cmd.get(0)
        if pod_num is None:
            return
        try:
            pod_num = int(pod_num)
        except ValueError:
            return

        # find the pod
        pod = None
        for p in self.k8s_inventory.last_pods:
            if p.num == pod_num:
                pod = p
                break
        if pod is None:
            return print("Pod number not found.")
        if pod.state.lower() != 'running':
            return print("Can't kill pod with state", pod.state)

        # check with the user
        ans = False
        while ans not in ("y", "n"):
            print("Will delete pod '%s' through kubernetes API. Continue ? [y/n]: " % pod)
            ans = input().lower()
        if ans != "y":
            return print("Cancelling")

        # kill the pod
        success = self.executor.kill_pod(pod, self.inventory)
        if success:
            print("Done")
        else:
            print(colored("Could not delete the pod", "red"))
