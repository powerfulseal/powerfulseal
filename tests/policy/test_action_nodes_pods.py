
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
import datetime
from mock import MagicMock

import pytest

# noinspection PyUnresolvedReferences
from tests.fixtures import noop_scenario, no_filtered_items_scenario
from tests.fixtures import make_dummy_object, dummy_object


def test_empty_property_criteria_dont_match(noop_scenario):
    assert noop_scenario.match_property(None, None) is False


@pytest.mark.parametrize("query,should_match",[
    ("abc", True),
    ("def", True),
    ("lol", False),
])
def test_matches_list_types(noop_scenario, dummy_object, query, should_match):
    dummy_object.list_attr = ["abc", "def"]
    criterion = {
        "name": "list_attr",
        "value": query,
    }
    assert should_match == noop_scenario.match_property(dummy_object, criterion)


def test_no_matched_items(noop_scenario):
    noop_scenario.execute()
    noop_scenario.filter.assert_not_called()
    noop_scenario.act.assert_not_called()


def test_no_filtered_items(no_filtered_items_scenario):
    no_filtered_items_scenario.execute()
    no_filtered_items_scenario.filter.assert_called()
    no_filtered_items_scenario.act.assert_not_called()


def test_filter_property(noop_scenario):
    ATTR_NAME = "test"
    dummy1 = make_dummy_object()
    setattr(dummy1, ATTR_NAME, "yes")
    dummy2 = make_dummy_object()
    setattr(dummy2, ATTR_NAME, "no")
    criterion = {
        "name": ATTR_NAME,
        "value": getattr(dummy2, ATTR_NAME)
    }
    assert noop_scenario.filter_property([dummy1, dummy2], criterion) == [dummy2]


@pytest.fixture
def some_datetime():
    dt = datetime.datetime.utcnow()
    return dt.replace(
        year = 2017,
        month = 12,
        day = 1,
        hour = 13,
        minute = 0,
        second = 0,
    )

@pytest.mark.parametrize("day,should_pass", [
    (1, True), # Friday
    (2, False), # Saturday
])
def test_filter_day_time_day_of_the_week(noop_scenario, some_datetime, day, should_pass):
    some_datetime = some_datetime.replace(day=day)
    criterion = {
        "onlyDays": [
            "friday",
        ],
        "startTime": {
            "hour": 0,
            "minute": 0,
            "second": 0
        },
        "endTime": {
            "hour": 23,
            "minute": 59,
            "second": 59
        },
    }
    candidates = [make_dummy_object(), make_dummy_object()]
    if should_pass:
        assert noop_scenario.filter_day_time(candidates, criterion, now=some_datetime) == candidates
    else:
        assert noop_scenario.filter_day_time(candidates, criterion, now=some_datetime) == []


@pytest.mark.parametrize("hour,minute,second, should_pass", [
    (1,0,0, False), # 1am is bad
    (9,0,1, True), # just in time
    (13,0,0, True), # 1pm is good
    (17,59,14, True), # last minute chaos !
    (17,59,30, False), # just too late
    (23,0,0, False), # 11pm is bad
])
def test_filter_day_time_of_day(noop_scenario, some_datetime, hour, minute,second, should_pass):
    some_datetime = some_datetime.replace(
        hour=hour,
        minute=minute,
        second=second,
    )
    criterion = {
        "onlyDays": [
            "friday",
        ],
        "startTime": {
            "hour": 9,
            "minute": 0,
            "second": 0
        },
        "endTime": {
            "hour": 17,
            "minute": 59,
            "second": 15
        },
    }
    candidates = [make_dummy_object(), make_dummy_object()]
    if should_pass:
        assert noop_scenario.filter_day_time(candidates, criterion, now=some_datetime) == candidates
    else:
        assert noop_scenario.filter_day_time(candidates, criterion, now=some_datetime) == []


def test_random_sample_size(noop_scenario):
    candidates = [make_dummy_object() for x in range(100)]
    for x in range(len(candidates)+1):
        sample = noop_scenario.filter_random_sample(candidates,{"size":x})
        assert len(sample) == x
        for elem in sample:
            assert elem in candidates


def test_random_sample_percentage(noop_scenario):
    candidates = [make_dummy_object() for x in range(100)]
    for x in range(101):
        percentage = x / 100.00
        sample = noop_scenario.filter_random_sample(candidates,{"ratio":percentage})
        assert len(sample) == int(percentage * len(candidates))
        for elem in sample:
            assert elem in candidates


def test_random_doesnt_pass_on_empty_criterion(noop_scenario):
    candidates = [make_dummy_object() for x in range(100)]
    for x in range(101):
        sample = noop_scenario.filter_random_sample(candidates,None)
        assert len(sample) == 0


@pytest.mark.parametrize("proba", [
    0.3,
    0.1,
    0.5,
    0.9
])
def test_filter_probability(noop_scenario, proba):
    random.seed(7) # make the tests deterministic
    SAMPLES = 100000
    candidates = [make_dummy_object(), make_dummy_object()]
    agg_len = 0.0
    criterion = {"probabilityPassAll": proba}
    for _ in range(SAMPLES):
        agg_len += len(noop_scenario.filter_probability(candidates, criterion))
    assert (agg_len/len(candidates))/SAMPLES == pytest.approx(proba, 0.01)


@pytest.mark.parametrize("sleep_time", [
    0, 1.0, 5
])
def test_action_wait(monkeypatch, noop_scenario, sleep_time):
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)
    criterion = {
        "seconds": sleep_time
    }
    noop_scenario.action_wait({}, criterion)
    assert sleep_mock.call_count == 1
    assert sleep_mock.call_args[0] == (sleep_time,)


def test_filter_mapping_uses_the_mapping(noop_scenario):
    dummy = make_dummy_object()
    items = [dummy]
    mapping = {
        "filterA": MagicMock(return_value=items),
        "filterB": MagicMock(return_value=[]),
    }
    filters = [
        {"filterA": {},},
        {"filterB": {},},
    ]
    res = noop_scenario.filter_mapping(items, filters, mapping)
    assert res == []
    assert mapping.get("filterA").call_count == 1
    assert mapping.get("filterA").call_args[0] == (items,{})
    assert mapping.get("filterB").call_count == 1
    assert mapping.get("filterB").call_args[0] == (items,{})


def test_acts_mapping_only_waits_once(noop_scenario):
    items = [make_dummy_object(), make_dummy_object()]
    mapping = {
        "wait": MagicMock(return_value=[]),
    }
    actions = [
        {"wait": {},},
    ]
    noop_scenario.act_mapping(items, actions, mapping)
    assert mapping.get("wait").call_count == 1
