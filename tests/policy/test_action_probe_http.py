
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
from mock import MagicMock, patch


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

def test_get_url_all_params(action_probe_http):
    schema = dict(
        target=dict(
            url="http://10.10.10.10:80"
        ),
        headers=[dict(name="TEST", value="SOMETHING")],
        method="POST",
        body="SOMEBODY here!",
        timeout=2000,
        insecure=True,
    )
    action_probe_http.schema = schema
    mock_request = MagicMock()

    with patch("requests.request", mock_request):
        action_probe_http.execute()

    assert mock_request.call_count == 1
    args = mock_request.call_args
    assert args.args == ('POST', 'http://10.10.10.10:80/')
    assert args.kwargs == dict(headers={'TEST': 'SOMETHING'}, verify=False, timeout=2.0, data=b'SOMEBODY here!', proxies={'http': '', 'https': ''})

def test_get_url_proxy(action_probe_http):
    schema = dict(
        target=dict(
            url="http://10.10.10.10:80"
        ),
        proxy="http://some.proxy.com:8080"
    )
    action_probe_http.schema = schema
    mock_request = MagicMock()

    with patch("requests.request", mock_request):
        action_probe_http.execute()

    assert mock_request.call_count == 1
    args = mock_request.call_args
    assert args.args == ('GET', 'http://10.10.10.10:80/')
    assert args.kwargs == dict(headers={}, timeout=1.0, data=b'', verify=True, proxies={'http': "http://some.proxy.com:8080", 'https': "http://some.proxy.com:8080"})
