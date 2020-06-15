import unittest
from powerfulseal.k8s.k8s_inventory import K8sInventory

import mock


def test_get_pod_metrics():

    class Item(object):
        def __init__(self, metadata):
            self.metadata = metadata

    class MetaData(object):
        def __init__(self,  name):

            self.name = name

    meta = MetaData("openshift-test")
    item = Item(meta)
    meta1 = MetaData("openshift-two")
    item1 = Item(meta1)

    meta2 = MetaData("openshift-three")
    item2 = Item(meta2)
    meta3 = MetaData("openshift-four")
    item3 = Item(meta3)
    mocked_data = lambda: [item, item1, item2, item3]

    with mock.patch('powerfulseal.k8s.k8s_client') as k8s_client:
        k8s_client.list_namespaces = mocked_data
        k8s_inventory = K8sInventory(k8s_client)
        result = K8sInventory.get_regex_namespaces(k8s_inventory, ".*shift-t.*")
        print('result ' + str(result))
        assert len(result) == 3
        assert "openshift-test" in result
        assert "openshift-two" in result
        assert "openshift-three" in result
        assert "openshift-four" not in result