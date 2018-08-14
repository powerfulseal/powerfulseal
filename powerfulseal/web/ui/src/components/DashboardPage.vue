<template>
    <div>
        <b-card>
            <template slot="header">
                <font-awesome-icon icon="robot"/>
                Autonomous Mode
            </template>

            <div v-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.LOADING">
                <font-awesome-icon icon="spinner" spin/>
            </div>
            <div v-else>
                <div>
                    <strong>Status:</strong>
                    <span v-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STOPPED">
                        Stopped
                    </span>
                    <span v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STARTING">
                        Starting
                    </span>
                    <span v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STOPPING">
                        Stopping
                    </span>
                    <span v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STARTED">
                        Started
                    </span>
                    <span v-else>
                        Error
                    </span>
                </div>
            </div>

            <template slot="footer">
                <b-button v-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STOPPED" @click="toggleRunning()" variant="success">
                    Start
                </b-button>
                <b-button v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STARTING" disabled="disabled" variant="success">
                    Start
                </b-button>
                <b-button v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STOPPING" disabled="disabled" variant="danger">
                    Stop
                </b-button>
                <b-button v-else-if="autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STARTED" @click="toggleRunning()" variant="danger">
                    Stop
                </b-button>
                <b-button v-else disabled="disabled">
                    Start
                </b-button>
                <b-button class="ml-1" variant="primary" @click="$store.dispatch('getAutonomousModeStatus')">
                    Refresh
                </b-button>
            </template>
        </b-card>
        <b-card>
            <template slot="header">
                <font-awesome-icon icon="align-justify" v-show="isLogsLoaded"/>
                <font-awesome-icon icon="spinner" spin v-show="!isLogsLoaded"/>
                Logs
                <b-button class="float-right" size="sm" variant="primary" @click="$store.dispatch('updateLogs')" :disabled="!isLogsLoaded">
                    Refresh
                </b-button>
            </template>
            <div class="my-1">
                <b-form-group class="ml-0 mb-0">
                    <b-input-group>
                        <b-form-input @input="filterDebounce" id="filter" placeholder="Filter logs"></b-form-input>
                    </b-input-group>
                </b-form-group>
            </div>
            <b-table :items="logEntries"
                     :fields="logs.fields"
                     :filter="logs.filter"
                     :current-page="logs.currentPage"
                     :per-page="12"
                     sort-by="timestamp"
                     :sort-desc="true"
                     ref="table">
                <template slot="timestamp" slot-scope="row">{{row.value | formatTimestamp}}</template>
                <template slot="level" slot-scope="row">{{row.value}}</template>
                <template slot="message" slot-scope="row">{{row.value}}</template>
            </b-table>

            <b-row>
                <b-col md="6">
                    <b-pagination :total-rows="logEntries.length"
                                  :per-page="12"
                                  v-model="logs.currentPage"></b-pagination>
                </b-col>
            </b-row>

        </b-card>
    </div>
</template>

<script>
import {mapState} from 'vuex'
import constants from '../constants.js'
import moment from 'moment'
import _ from 'lodash'

export default {
  name: 'dashboard-page',
  data: function () {
    return {
      constants,
      logs: {
        currentPage: 0,
        fields: [
          {key: 'timestamp', value: 'Timestamp'},
          {key: 'level', value: 'Level'},
          {key: 'message', value: 'Message'}
        ],
        filter: ''
      }
    }
  },
  methods: {
    toggleRunning () {
      if (this.autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STOPPED) {
        this.$store.dispatch('startAutonomousMode')
      } else if (this.autonomousModeStatus === constants.AUTONOMOUS_MODE_STATUS.STARTED) {
        this.$store.dispatch('stopAutonomousMode')
      }
    },
    filterDebounce: _.debounce(function (val) {
      this.logs.filter = val
    }, 1000)
  },
  computed: mapState({
    autonomousModeStatus: state => state.dashboard.autonomousModeStatus,
    logEntries: state => state.dashboard.logs,
    isLogsLoaded: state => state.dashboard.isLogsLoaded
  }),
  filters: {
    formatTimestamp (value) {
      return moment(value * 1000).fromNow()
    }
  },
  created () {
    this.$store.dispatch('getAutonomousModeStatus')
    this.$store.dispatch('updateLogs')
  }
}
</script>
