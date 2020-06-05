
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

from powerfulseal import makeLogger
import spur
import random

from .abstract_executor import AbstractExecutor


class SSHExecutor(AbstractExecutor):
    """ Executes commands on Node instances via SSH.
        Assumes password-less setup.
    """

    PREFIX = ["sh", "-c"]
    DEFAULT_KILL_COMMAND = "sudo docker kill -s {signal} {container_id}"

    def __init__(self, nodes=None, user="cloud-user",
                 ssh_allow_missing_host_keys=False, ssh_path_to_private_key=None,
                 ssh_password=None, ssh_kill_command=None, override_host=None,
                 use_private_ip=False, logger=None):
        self.nodes = nodes or []
        self.user = user
        self.missing_host_key = (spur.ssh.MissingHostKey.accept
                                 if ssh_allow_missing_host_keys
                                 else spur.ssh.MissingHostKey.raise_error)
        self.ssh_path_to_private_key = ssh_path_to_private_key
        self.ssh_password = ssh_password
        self.ssh_kill_command = ssh_kill_command or self.DEFAULT_KILL_COMMAND
        self.override_host = override_host
        self.use_private_ip = use_private_ip
        self.logger = logger or makeLogger(__name__)

    def execute(self, cmd, nodes=None, use_private_ip=None, debug=False):
        """
            Executes an arbitrary command, prefixed with sh -c, on each node
        """
        nodes = nodes or self.nodes
        use_private_ip = use_private_ip or self.use_private_ip
        results = dict()
        cmd_full = self.PREFIX + [cmd]
        for node in nodes:
            hostip = node.extIp
            if use_private_ip:
                hostip = node.ip
            if self.override_host:
                hostip = self.override_host
            if self.ssh_password is not None:
                shell = spur.SshShell(
                    hostname=hostip,
                    username=self.user,
                    missing_host_key=self.missing_host_key,
                    password=self.ssh_password,
                )
            else:
                shell = spur.SshShell(
                    hostname=hostip,
                    username=self.user,
                    missing_host_key=self.missing_host_key,
                    private_key_file=self.ssh_path_to_private_key,
                )

            self.logger.debug("Executing '%s' on %s" % (cmd_full, node.name))
            try:
                with shell:
                    output = shell.run(cmd_full)
                    results[hostip] = {
                        "ret_code": output.return_code,
                        "stdout": output.output.decode('utf-8'),
                        "stderr": output.stderr_output.decode('utf-8'),
                    }
            except Exception as e:
                results[hostip] = {
                    "ret_code": 1,
                    "error": str(e),
                }
                self.logger.error("Executing '%s' on %s failed with error: %s" % (cmd_full, node.name, str(e)))
        return results

    def get_kill_command(self, container_id, signal=None):
        """ Produces a templated command to execute """
        return self.ssh_kill_command.format(signal=str(signal or "SIGKILL"), container_id=str(container_id))

    def kill_pod(self, pod, inventory, signal=None):
        # Find node to execute SSH on
        node = inventory.get_node_by_ip(pod.host_ip)
        if node is None:
            self.logger.info("Node not found for pod: %s", pod)
            return False
        # Format command
        container_id = random.choice(pod.container_ids)
        cmd = self.get_kill_command(
            signal=signal,
            container_id=container_id.replace("docker://", ""),
        )
        # Execute command
        self.logger.debug("Action execute '%s' on %r", cmd, pod)
        for value in self.execute(cmd, nodes=[node]).values():
            if value["ret_code"] > 0:
                self.logger.error("Error return code: %s", value)
                return False

        return True
