<template>
    <div>
        <b-card>
            <b-modal ref="actionFailedModal"
                     :ok-only="true">
                The action attempted failed. For debug info, see console logs.
            </b-modal>

            <template slot="header">
                <font-awesome-icon icon="server" v-show="isNodesLoaded"/>
                <font-awesome-icon icon="spinner" spin v-show="!isNodesLoaded"/>
                Nodes
                <b-button class="float-right" size="sm" variant="primary" @click="updateNodes()" :disabled="!isNodesLoaded">
                    Refresh
                </b-button>
            </template>

            <div class="my-1">
                <b-form-group class="ml-0 mb-0">
                    <b-input-group>
                        <b-form-input v-model="nodesFilter" placeholder="Filter nodes"></b-form-input>
                        <b-input-group-append>
                            <b-button :disabled="!nodesFilter" @click="nodesFilter=''" variant="primary">Clear</b-button>
                        </b-input-group-append>
                    </b-input-group>
                </b-form-group>
            </div>
            <b-table :items="nodes"
                     :fields="tableFields.nodes"
                     :filter="nodesFilter"
                     :current-page="currentNodesPage"
                     :per-page="10"
                     style="table-layout: fixed">
                <template slot="id" slot-scope="row">{{row.value}}</template>
                <template slot="name" slot-scope="row">{{row.value}}</template>
                <template slot="ip" slot-scope="row">{{row.value}}</template>
                <template slot="az" slot-scope="row">{{row.value}}</template>
                <template slot="groups" slot-scope="row">{{row.value}}</template>
                <template slot="state" slot-scope="row">{{constants.NODE_STATE_LABELS[row.value]}}</template>
                <template slot="actions" slot-scope="row">
                    <b-button :disabled="nodes[row.index].state !== constants.NODE_STATES.DOWN || isNodesChanging[row.index]"
                              class="btn btn-success mr-1"
                              @click="startNode(row.item._idInNodesArray)">
                        Start
                    </b-button>
                    <b-button :disabled="nodes[row.index].state !== constants.NODE_STATES.UP  || isNodesChanging[row.index]"
                              class="btn btn-danger"
                              @click="stopNode(row.item._idInNodesArray)">
                        Stop
                    </b-button>
                </template>
            </b-table>

            <b-row>
                <b-col md="6">
                    <b-pagination :total-rows="nodes.length"
                                  :per-page="10"
                                  v-model="currentNodesPage"></b-pagination>
                </b-col>
            </b-row>
        </b-card>
        <b-card>
            <template slot="header">
                <font-awesome-icon icon="database" v-show="isPodsLoaded"/>
                <font-awesome-icon icon="spinner" spin v-show="!isPodsLoaded"/>
                Pods
                <b-button class="float-right" size="sm" variant="primary" @click="updatePods()" :disabled="!isPodsLoaded">
                    Refresh
                </b-button>
            </template>

            <b-form-group class="ml-0 mb-0">
                <b-input-group>
                    <b-form-input v-model="podsNamespaceFilter" placeholder="Search by namespace"></b-form-input>
                    <b-input-group-append>
                        <b-button :disabled="!isPodsLoaded" @click="updatePods()" variant="primary">Search</b-button>
                    </b-input-group-append>
                </b-input-group>
            </b-form-group>

            <div class="my-1">
                <b-form-group class="ml-0 mb-0">
                    <b-input-group>
                        <b-form-input v-model="podsFilter" placeholder="Filter pods"></b-form-input>
                        <b-input-group-append>
                            <b-button :disabled="!podsFilter" @click="podsFilter=''" variant="primary">Clear</b-button>
                        </b-input-group-append>
                    </b-input-group>
                </b-form-group>
            </div>
            <b-table :items="pods"
                     :fields="tableFields.pods"
                     :filter="podsFilter"
                     :current-page="currentPodsPage"
                     :per-page="10"
                     style="table-layout: fixed">
                <template slot="id" slot-scope="row">{{row.value}}</template>
                <template slot="namespace" slot-scope="row">{{row.value}}</template>
                <template slot="container_ids" slot-scope="row">{{row.value | stringifyContainers }}</template>
                <template slot="ip" slot-scope="row">{{row.value}}</template>
                <template slot="host_ip" slot-scope="row">{{row.value}}</template>
                <template slot="labels" slot-scope="row">{{row.value}}</template>
                <template slot="state" slot-scope="row">{{row.value}}</template>
                <template slot="restart_count" slot-scope="row">{{row.value}}</template>
                <template slot="actions" slot-scope="row">
                    <b-button class="btn btn-danger mr-1"
                              :disabled="isPodsStopping[row.item._idInPodsArray]"
                              @click="killPod(row.item._idInPodsArray, false)">
                        Kill
                    </b-button>
                    <b-button class="btn btn-danger"
                              :disabled="isPodsStopping[row.item._idInPodsArray]"
                              @click="killPod(row.item._idInPodsArray, true)">
                        Force Kill
                    </b-button>
                </template>
            </b-table>

            <b-row>
                <b-col md="6">
                    <b-pagination :total-rows="pods.length"
                                  :per-page="10"
                                  v-model="currentPodsPage"></b-pagination>
                </b-col>
            </b-row>
        </b-card>
    </div>
</template>

<style scoped>
.fluid-text {
    word-break: break-all;
}
</style>

<script>
import constants from '../constants.js'
import {mapState} from 'vuex'

export default {
  name: 'items-page',
  data () {
    return {
      constants,
      tableFields: {
        nodes: [
          {key: 'id', label: 'ID'},
          {key: 'name', label: 'Name'},
          {key: 'ip', label: 'IP Address'},
          {key: 'az', label: 'AZ'},
          {key: 'groups', label: 'Groups'},
          {key: 'state', label: 'State'},
          {key: 'actions', label: 'Actions'}
        ],
        pods: [
          {key: 'name', label: 'Name'},
          {key: 'namespace', label: 'Namespace'},
          {key: 'container_ids', label: 'Containers', thStyle: {'max-width': '200px'}},
          {key: 'ip', label: 'IP Address'},
          {key: 'host_ip', label: 'Host IP'},
          {key: 'labels', label: 'Labels'},
          {key: 'state', label: 'State'},
          {key: 'restart_count', label: 'Restarts'},
          {key: 'actions', label: 'Actions'}
        ]
      },
      currentNodesPage: 0,
      currentPodsPage: 0,
      nodesFilter: '',
      podsFilter: '',
      podsNamespaceFilter: ''
    }
  },
  filters: {
    stringifyContainers (containers) {
      return containers.join('\n')
    }
  },
  methods: {
    startNode (index) {
      this.$store.dispatch('startNode', index).catch(() => {
        this.$refs.actionFailedModal.show()
      })
    },
    stopNode (index) {
      this.$store.dispatch('stopNode', index).catch(() => {
        this.$refs.actionFailedModal.show()
      })
    },
    killPod (index, isForced) {
      this.$store.dispatch('killPod', index, isForced).catch(() => {
        this.$refs.actionFailedModal.show()
      })
    },
    updateNodes () {
      this.$store.dispatch('updateNodes')
    },
    updatePods () {
      this.$store.dispatch('updatePods', this.$data.podsNamespaceFilter)
    }
  },
  computed: mapState({
    nodes: state => state.items.nodes,
    pods: state => state.items.pods,
    isNodesLoaded: state => state.items.isNodesLoaded,
    isPodsLoaded: state => state.items.isPodsLoaded,
    isPodsStopping: state => state.items.isPodsStopping,
    isNodesChanging: state => state.items.isNodesChanging
  }),
  created () {
    this.$store.dispatch('updateNodes')
    this.$store.dispatch('updatePods')
  }
}
</script>
