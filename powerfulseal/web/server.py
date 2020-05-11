# Copyright 2018 Bloomberg Finance L.P.
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
import logging
import random
import time
import threading

import jsonschema
import yaml
from flask import Flask, jsonify, request, send_file, render_template
from flask_cors import CORS

from powerfulseal.policy import PolicyRunner
from powerfulseal.policy.node_scenario import NodeScenario
from powerfulseal.policy.pod_scenario import PodScenario

from werkzeug.middleware.proxy_fix import ProxyFix

# Flask instance and routes
app = Flask(__name__, static_url_path="/static", static_folder="dist/static", template_folder="dist")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# singleton for a minute
config = dict()

@app.route('/logs')
def logs():
    logs = config.get("logger").logs
    print(logs)
    return render_template('logs.html.j2',
        title="",
        logs=logs,
    )


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    return render_template('index.html.j2',
        title="",
        policy=yaml.dump(config.get("policy")),
    )


def start_server(host, port, policy, accept_proxy_headers=False, logger=None):
    if accept_proxy_headers:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
    config["policy"] = policy
    config["logger"] = logger
    threading.Thread(target=app.run, args=(host, port)).start()

class ServerStateLogHandler(logging.Handler):
    def __init__(self, max=100):
        logging.Handler.__init__(self)
        self.logs = []
        self.max = max

    def emit(self, record):
        self.logs.append({
            'timestamp': record.created,
            'level': record.levelname,
            'message': record.getMessage()
        })
        self.logs = self.logs[-self.max:]
