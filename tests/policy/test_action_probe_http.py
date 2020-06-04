
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


import random
import pytest
from mock import MagicMock


# noinspection PyUnresolvedReferences
from tests.fixtures import action_probe_http


def test_get_url_simple(action_probe_http):
    mock_resp = MagicMock()
    schema = dict(
        target=dict(
            url="http://10.10.10.10:80"
        )
    )
    url = action_probe_http.get_url(schema)
    assert url == "http://10.10.10.10:80/"

def test_get_url_service(action_probe_http):
    mock_resp = MagicMock()
    mock_resp.spec.cluster_ip = "10.10.10.2"
    action_probe_http.k8s_inventory.get_service = MagicMock(
        return_value=mock_resp
    )

    schema = dict(
        target=dict(
            service=dict(
                name="somename",
                namespace="somenamespace",
            )
        )
    )

    url = action_probe_http.get_url(schema)

    assert url == "http://10.10.10.2:80/"
    assert action_probe_http.k8s_inventory.get_service.call_count == 1
    assert action_probe_http.k8s_inventory.get_service.call_args == (dict(
        name=schema.get("target").get("service").get("name"),
        namespace=schema.get("target").get("service").get("namespace"),
    ),)
