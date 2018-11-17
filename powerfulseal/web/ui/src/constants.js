export default {
  AUTONOMOUS_MODE_STATUS: {
    STARTED: 0,
    STOPPED: 1,
    STARTING: 3,
    STOPPING: 4,
    LOADING: 5,
    ERROR: 6
  },
  INVENTORY_GROUP_TYPES: {
    ALL_NODES: 0,
    INVENTORY_FILE: 1
  },
  INVENTORY_GROUP_TYPE_LABELS: {
    0: 'All Nodes',
    1: 'Inventory File'
  },
  CLOUD_DRIVERS: {
    OPENSTACK: 0,
    AWS: 1,
    NONE: 2
  },
  CLOUD_DRIVER_LABELS: {
    0: 'OpenStack',
    1: 'AWS',
    2: 'None'
  },
  METRIC_COLLECTORS: {
    NONE: 0,
    PROMETHEUS: 1
  },
  METRIC_COLLECTOR_LABELS: {
    0: 'None',
    1: 'Prometheus'
  },
  RANDOM_SAMPLE: {
    DISABLED: 0,
    SIZE: 1,
    RATIO: 2
  },
  NODE_ACTION_TYPES: {
    STOP: 0,
    START: 1,
    WAIT: 2,
    EXECUTE: 3
  },
  NODE_ACTION_TYPE_LABELS: {
    0: 'Stop',
    1: 'Start',
    2: 'Wait',
    3: 'Execute'
  },
  POD_ACTION_TYPES: {
    KILL: 0,
    WAIT: 1
  },
  POD_ACTION_TYPE_LABELS: {
    0: 'Kill',
    1: 'Wait'
  },
  POD_MATCHER_TYPES: {
    NAMESPACE: 0,
    DEPLOYMENT: 1,
    LABELS: 2
  },
  POD_MATCHER_LABELS: {
    0: 'Namespace',
    1: 'Deployment',
    2: 'Labels'
  },
  NODE_STATES: {
    UNKNOWN: 1,
    UP: 2,
    DOWN: 3
  },
  NODE_STATE_LABELS: {
    1: 'Unknown',
    2: 'Up',
    3: 'Down'
  }
}
