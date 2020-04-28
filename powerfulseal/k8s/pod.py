
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




class Pod():
    """ Internal representation of a pod. Use to easily manipulate them
        internally.
    """

    def __init__(self, name, namespace, num=None, uid=None, host_ip=None, ip=None,
                container_ids=None, restart_count=None, state=None, labels=None, annotations=None, meta=None):
        self.name = name
        self.namespace = namespace
        self.num = num
        self.uid = uid
        self.host_ip = host_ip
        self.ip = ip
        self.container_ids = container_ids or []
        self.restart_count = restart_count or 0
        self.state = state
        self.labels = labels or dict()
        self.annotations = annotations or dict()
        self.meta = meta

    def __str__(self):
        return (
            "[pod #{num} name={name} namespace={namespace} containers={containers} ip={ip} host_ip={host_ip} "
            "state={state} labels:{labels} annotations:{annotations}]"
        ).format(
            num=self.num,
            name=self.name,
            namespace=self.namespace,
            containers=len(self.container_ids),
            ip=self.ip,
            host_ip=self.host_ip,
            state=str(self.state),
            labels=",".join(["%s=%s" % (k,v) for k,v in self.labels.items()]),
            annotations=",".join(["%s=%s" % (k,v) for k,v in self.annotations.items()]),
        )

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        if self.uid:
            return hash(self.uid)
        return hash(self.name + self.namespace)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()
    
    def get_label_or_annotation(self, key, default):
        return self.labels.get(key) or self.annotations.get(key) or default
