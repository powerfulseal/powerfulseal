
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

# This alert manager action uses https://github.com/prometheus/alertmanager#api v2

from powerfulseal import makeLogger

from ..metriccollectors.stdout_collector import StdoutCollector
from .action_abstract import ActionAbstract
from datetime import datetime, timedelta
import requests

# Action class to delete generated silences in ActionAlertManager
class ActionUnmuteAlertManager():
    def __init__(self, name, silence_id, alertmanager_url, proxies={}, logger=None):
        self.name = name
        self.logger = logger or makeLogger(__name__, name)
        self.silence_id = silence_id
        self.alertmanager_url = alertmanager_url
        self.proxies = proxies

    def execute(self):
        url = self.alertmanager_url + '/silence/' + self.silence_id
        self.logger.info("Unmuting alerts for alert manager %s", self.alertmanager_url)
        success = False
        try:
            resp = requests.request(
                method="DELETE",
                url=url,
                proxies=dict(
                    http=self.proxies.get("http", ""),
                    https=self.proxies.get("https", "")
                ),
                verify=False,
            )
            resp.raise_for_status()
            success = True
        except:
            self.logger.exception("Exception while calling %s", url)
        return success
 

class ActionAlertManager(ActionAbstract):

    def __init__(self, name, schema, logger=None, metric_collector=None):
        self.name = name
        self.schema = schema
        self.logger = logger or makeLogger(__name__, name)
        self.metric_collector = metric_collector or StdoutCollector()
        self.targets = self.schema.get("targets", [])
        self.proxies = self.schema.get("proxies", {})
        self.silences = dict()
        # build a url indexed map to store generated silences in mute action
        for target in self.targets:
            url = target.get("url", None)
            if url is not None:
                self.silences[url] = None
        self.action_mapping = {
            "mute": self.action_mute
        }
        self.cleanup_actions = []

    def execute(self):
        actions = self.schema.get("actions", [])
        self.logger.info("executing alertmanager actions...")

        success = True
        for action in actions:
            for key, method in self.action_mapping.items():
                if key in action:
                    params = action.get(key)
                    ret = method(params)
                    if not ret:
                        success = False
        return success

    def action_mute(self, params):
        success = True
        # automute is True unless explicitly set to False
        autoUnmute = params.get('autoUnmute', True) if type(params) is dict else True
        for alert_manager in self.silences:
            self.silences[alert_manager] = self.mute(alert_manager)
            if self.silences[alert_manager] is not None:
                if autoUnmute is True:
                    # add unmute action for cleaning up when mute action generates silence
                    # and `autoUnmute` is True
                    self.cleanup_actions.append(
                        ActionUnmuteAlertManager(
                            name=self.name,
                            silence_id=self.silences[alert_manager],
                            alertmanager_url=alert_manager,
                            proxies=self.proxies
                    ))
            elif success:
                success = False
        return success


    def mute(self, url):
        self.logger.info("Silencing alerts for alert manager %s", url)
        startTime = datetime.now()
        # mute all alerts for 15 mins (900 secs)
        endTime = startTime + timedelta(seconds=900)
        payload = {
            'comment': 'silence all alerts',
            'createdBy': 'powerfulseal',
            'startsAt': startTime.isoformat(),
            'endsAt': endTime.isoformat(),
            'matchers': [
                {
                    'isRegex': True,
                    'name': 'alertname',
                    'value': '.+'
                }
            ]
        }
        url = url + '/silences'
        silenceId = None
        try:
            resp = requests.request(
                method="POST",
                url=url,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "powefulseal"
                },
                proxies=dict(
                    http=self.proxies.get("http", ""),
                    https=self.proxies.get("https", "")
                ),
                json=payload,
                verify=False,
            )
            resp.raise_for_status()
            silenceId = resp.json()['silenceID']
        except:
            self.logger.exception("Exception while calling %s", url)
        return silenceId

    # required to finish cleaning up (removing generated silences)
    def get_cleanup_actions(self):
        return self.cleanup_actions
