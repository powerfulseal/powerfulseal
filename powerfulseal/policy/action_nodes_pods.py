
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


import time
import re
from datetime import datetime
import calendar
import random
from powerfulseal import makeLogger

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_abstract import ActionAbstract


class ActionNodesPods(ActionAbstract):
    """ Basic class to represent a single testing scenario.

        This is a base class, containing some shared filters, shouldn't be
        used by itself. It's extended for both node and pod scenarios.
    """

    def __init__(self, name, schema, logger=None, metric_collector=None):
        self.name = name
        self.schema = schema
        self.logger = logger or makeLogger(__name__, name)
        self.metric_collector = metric_collector or StdoutCollector()
        self.action_mapping = dict()

    def execute(self):
        """ Main entry point to starting a scenario.

            It calls .match() to compute the intial set of items,
            then goes through all the filters in sequence,
            and finally executes all the actions on all remaining items.
        """
        initial_set = self.match()
        self.logger.debug("Initial set: %r", initial_set)
        self.logger.info("Initial set length: %d", len(initial_set))
        if initial_set:
            filtered_set = self.filter(initial_set)
            self.logger.debug("Filtered set: %r", filtered_set)
            self.logger.info("Filtered set length: %d", len(filtered_set))
            if not filtered_set:
                return True
            ret = self.act(filtered_set)
            if not ret:
                return False
        else:
            self.metric_collector.add_filtered_to_empty_set_metric()
        self.logger.debug("Done")
        return True

    def match(self):
        """ Reads the policy and returns the initial set of items.
        """
        return [] # pragma: no cover

    def match_property(self, candidate, criterion):
        """ Helper method to match a property following some criterion.
            Turns the value into a regular expression.
        """
        if not criterion:
            return False
        name = criterion.get("name")
        value = getattr(candidate, name)
        negative = criterion.get("negative", False)
        expr = re.compile(criterion.get("value"), re.IGNORECASE)
        # support single values or list of values
        if type(value) is not list:
            value = [value]
        # if negative, reverse the condition
        if negative:
            return all([
                not expr.match(str(v))
                for v in value
            ])
        # otherwise do match for any values in the list
        return any([
            expr.match(str(v))
            for v in value
        ])

    def filter(self, items):
        """ Applies various filters based on the given policy.
        """
        filters = self.schema.get("filters", [])
        mapping = {
            "property": self.filter_property,
            "dayTime": self.filter_day_time,
            "randomSample": self.filter_random_sample,
            "probability": self.filter_probability,
        }
        return self.filter_mapping(items, filters, mapping)

    def filter_property(self, candidates, criterion):
        """ Filters out things which don't match their property filters.
        """
        return [
            candidate for candidate in candidates
            if self.match_property(candidate, criterion)
        ]

    def filter_day_time(self, candidates, criterion, now=None):
        """ Passed unchanged list of candidates, if the execution time
            satisfies the policy requirements.
        """
        now = now or datetime.now()
        self.logger.debug("Now is %r", now)

        # check the day is permitted
        day_name = calendar.day_name[now.weekday()].lower()
        permitted_days = criterion.get("onlyDays", [])
        if permitted_days and day_name not in permitted_days:
            self.logger.info("Not allowed on %s", day_name)
            return []

        # check the time is not too early
        start = criterion.get("startTime", {})
        start_date = now.replace(
            hour=start.get("hour", 10),
            minute=start.get("minute", 0),
            second=start.get("second", 0),
        )
        if now < start_date:
            self.logger.info("Too early")
            return []

        # check the time is not too late
        end = criterion.get("endTime", {})
        end_date = now.replace(
            hour=end.get("hour", 15),
            minute=end.get("minute", 59),
            second=end.get("second", 59),
        )
        if now > end_date:
            self.logger.info("Too late")
            return []

        return candidates

    def filter_random_sample(self, candidates, criterion):
        """ Returns a random sample from the initial list.
            It supports policy `size` and `ratio` features.
        """
        if not criterion:
            return []
        size = criterion.get("size")
        if size is None:
            ratio = criterion.get("ratio", 1)
            size = int(len(candidates)*ratio)
        if size == 0:
            self.logger.debug("RandomSample size 0")
            return []
        if size > len(candidates):
            return candidates
        return random.sample(candidates, size)

    def filter_probability(self, candidates, criterion):
        """ Returns the initial set unchanged with given probability.
            Returns empty list otherwise.
        """
        proba = float(criterion.get("probabilityPassAll", 0.5))
        if random.random() > proba:
            self.metric_collector.add_probability_filter_passed_no_nodes_filter()
            return []
        return candidates

    def filter_mapping(self, items, filters, mapping):
        """ Executes filters mapped to methods, based on policy keywords.
        """
        for criterion in filters:
            filter_method = None
            filter_params = None
            for filter_type in mapping.keys():
                if filter_type in criterion:
                    filter_method = mapping.get(filter_type)
                    filter_params = criterion.get(filter_type)
                    len_before = len(items)
                    items = filter_method(items, filter_params)
                    len_after = len(items)
                    self.logger.debug("Filter %s: %d -> %d items", filter_type, len_before, len_after)
                    break
            if not items:
                self.logger.info("Empty set after %r", criterion)
                break

        if not items:
            self.metric_collector.add_filtered_to_empty_set_metric()

        return items

    def action_wait(self, items, params):
        """ Waits x seconds, according to the policy.
        """
        sleep_time = params.get("seconds", 0)
        self.logger.info("Action sleep for %s seconds", sleep_time)
        time.sleep(sleep_time)

    def act(self, items):
        """ Execute policy's actions on the items
        """
        self.logger.debug("Acting on these: %r", items)
        actions = self.schema.get("actions", [])
        return self.act_mapping(items, actions, self.action_mapping)

    def act_mapping(self, items, actions, mapping):
        """ Executes all the actions on the list of pods.
        """
        success = True
        for action in actions:
            for key, method in mapping.items():
                if key in action:
                    params = action.get(key)
                    ret = method(items, params)
                    if not ret:
                        success = False
        return success


