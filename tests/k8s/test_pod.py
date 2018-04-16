from powerfulseal.k8s import Pod

EXAMPLE_POD_ARGS1 = dict(
    uid="someid",
    name="name of some kind",
    namespace="default",
)
EXAMPLE_POD_ARGS2 = dict(
    name="name of some kind",
    namespace="default",
)


def test_pods_are_deduplicated_with_uids():
    collection = set()
    collection.add(Pod(**EXAMPLE_POD_ARGS1))
    collection.add(Pod(**EXAMPLE_POD_ARGS1))
    assert len(collection) == 1

def test_pods_are_deduplicated_without_uids():
    collection = set()
    collection.add(Pod(**EXAMPLE_POD_ARGS2))
    collection.add(Pod(**EXAMPLE_POD_ARGS2))
    assert len(collection) == 1
