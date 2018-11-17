<template>
    <div>
        <b-modal ref="confirmationModal"
                 @hide="onConfirmationModalHide"
                 @hidden="onConfirmationModalHidden">
            You are about to overwrite your server's configuration file with your changes. Are you sure you want to continue?
        </b-modal>
        <b-modal ref="saveFailedModal"
                 :ok-only="true">
            Your changes could not be processed. For debug info, see console logs.
        </b-modal>
        <b-modal ref="saveCompleteModal"
                 :ok-only="true">
            Your changes have successfully been saved.
        </b-modal>
        <b-modal ref="exportModal"
                 :ok-only="true"
                 ok-title="Close">
            <pre v-highlightjs="policyYaml"><code class="yaml"></code></pre>
        </b-modal>
        <b-card>
            <template slot="header">
                <font-awesome-icon icon="cog"/>
                Configuration
            </template>
            <div v-if="isPolicyLoaded">
                <b-form>
                    <h4>Time Between Runs</h4>

                    <b-form-group horizontal
                                  :label-cols="2"
                                  breakpoint="md"
                                  label="Min Seconds"
                                  label-for="minSecondsBetweenRuns">
                        <b-form-input id="minSecondsBetweenRuns"
                                      type="number"
                                      v-model.trim.number="mutableConfig.minSecondsBetweenRuns">
                        </b-form-input>
                    </b-form-group>

                    <b-form-group horizontal
                                  :label-cols="2"
                                  breakpoint="md"
                                  label="Max Seconds"
                                  label-for="maxSecondsBetweenRuns">
                        <b-form-input id="maxSecondsBetweenRuns"
                                      type="number"
                                      v-model.trim.number="mutableConfig.maxSecondsBetweenRuns">
                        </b-form-input>
                    </b-form-group>

                    <h4>Node Scenarios</h4>
                    <b-form-group>
                        <b-table :items="mutableConfig.nodeScenarios"
                                 :fields="tableFields.nodeScenario">
                            <template slot="name" slot-scope="row">{{row.value}}</template>
                            <template slot="actions" slot-scope="row">
                                <b-button size="sm"
                                          class="mr-1"
                                          variant="primary"
                                          @click.stop="editNodeScenario(false, row.index)">
                                    Edit
                                </b-button>
                                <b-button size="sm"
                                          variant="danger"
                                          @click.stop="deleteNodeScenario(row.index)">
                                    Delete
                                </b-button>
                            </template>
                        </b-table>

                        <b-button size="md"
                                  variant="success"
                                  @click.stop="editNodeScenario(true, -1)">
                            Add
                        </b-button>
                    </b-form-group>

                    <b-form-group>
                        <h4>Pod Scenarios</h4>
                        <b-table :items="mutableConfig.podScenarios"
                                 :fields="tableFields.podScenario">
                            <template slot="name" slot-scope="row">{{row.value}}</template>
                            <template slot="actions" slot-scope="row">
                                <b-button size="sm"
                                          class="mr-1"
                                          variant="primary"
                                          @click.stop="editPodScenario(false, row.index)">
                                    Edit
                                </b-button>
                                <b-button size="sm"
                                          variant="danger"
                                          @click.stop="deletePodScenario(row.index)">
                                    Delete
                                </b-button>
                            </template>
                        </b-table>

                        <b-button size="md"
                                  variant="success"
                                  @click.stop="editPodScenario(true, -1)">
                            Add
                        </b-button>
                    </b-form-group>

                </b-form>
            </div>
            <div v-else>
                <font-awesome-icon icon="spinner" size="2x" spin/>
            </div>
            <template slot="footer">
                <button @click="handleSave"
                        :disabled="isSaveButtonDisabled || !isPolicyLoaded"
                        type="button"
                        class="btn btn-danger mr-1">
                    Save and Overwrite
                </button>
                <button @click="handleExport"
                        :disabled="isSaveButtonDisabled || !isPolicyLoaded"
                        type="button"
                        class="btn btn-primary mr-1">
                    Export Changes to YAML
                </button>
                <button @click="handleDiscard"
                        :disabled="isSaveButtonDisabled || !isPolicyLoaded"
                        type="button"
                        class="btn btn-secondary">
                    Discard
                </button>
            </template>
        </b-card>
        <node-scenario-modal
                ref="nodeScenarioModal"
                @updated="handleNodeScenarioUpdated"/>
        <pod-scenario-modal
                ref="podScenarioModal"
                @updated="handlePodScenarioUpdated"/>
    </div>
</template>

<script>
import constants from '../constants.js'
import NodeScenarioModal from './NodeScenarioModal'
import PodScenarioModal from './PodScenarioModal'
import Vue from 'vue'
import {mapState} from 'vuex'

export default {
  components: {
    NodeScenarioModal,
    PodScenarioModal
  },
  name: 'configuration-page',
  methods: {
    onConfirmationModalHide (evt) {
      this.configurationModalHiddenTrigger = evt.trigger
    },
    onConfirmationModalHidden (evt) {
      // Handles the case where the user confirms Save and Overwrite. If the
      // confirmation is hidden with the event trigger being 'ok', then the user
      // has confirmed the overwrite.
      // The `hidden` event is captured to achieve this as opposed to the `ok`
      // event to ensure the confirmation modal is still not open to conflict
      // with the success/failure modals.
      if (this.configurationModalHiddenTrigger === 'ok') {
        this.isSaveButtonDisabled = true
        this.$store.dispatch('saveConfig', this.mutableConfig).then(() => {
          this.$refs.saveCompleteModal.show()
        }).catch(() => {
          this.$refs.saveFailedModal.show()
        }).finally(() => {
          this.isSaveButtonDisabled = false
        })
      }
    },
    handleSave () {
      this.$refs.confirmationModal.show()
    },
    handleExport () {
      this.isSaveButtonDisabled = true
      this.$store.dispatch('exportYaml', this.mutableConfig).then(() => {
        this.$refs.exportModal.show()
      }).catch(() => {
        this.$refs.saveFailedModal.show()
      })
      this.isSaveButtonDisabled = false
    },
    handleDiscard () {
      this.$store.commit('resetMutableConfig')
    },
    handleNodeScenarioUpdated (scenario) {
      // The same modal is opened when creating a new node scenario, hence both cases need to be handled
      if (this.modalOptions.isCreatingNodeScenario) {
        this.mutableConfig.nodeScenarios.push(scenario)
      } else {
        // Vue.set is called to update all keys in the node scenario due to the design of reactivity in Vue
        Object.keys(this.mutableConfig.nodeScenarios[this.modalOptions.selectedNodeScenarioIndex]).forEach((key) => {
          Vue.set(this.mutableConfig.nodeScenarios[this.modalOptions.selectedNodeScenarioIndex], key, scenario[key])
        })
      }
    },
    editNodeScenario (isNewScenario, index) {
      // Opens the new node scenario modal; if a new one should be created, we pass in a default object
      this.modalOptions.isCreatingNodeScenario = isNewScenario
      if (isNewScenario) {
        this.$refs.nodeScenarioModal.openModal(NodeScenarioModal.DEFAULT_NODE_SCENARIO)
      } else {
        this.modalOptions.selectedNodeScenarioIndex = index
        this.$refs.nodeScenarioModal.openModal(this.mutableConfig.nodeScenarios[index])
      }
    },
    deleteNodeScenario (index) {
      this.$delete(this.mutableConfig.nodeScenarios, index)
    },
    handlePodScenarioUpdated (scenario) {
      if (this.modalOptions.isCreatingPodScenario) {
        this.mutableConfig.podScenarios.push(scenario)
      } else {
        Object.keys(this.mutableConfig.podScenarios[this.modalOptions.selectedPodScenarioIndex]).forEach((key) => {
          Vue.set(this.mutableConfig.podScenarios[this.modalOptions.selectedPodScenarioIndex], key, scenario[key])
        })
      }
    },
    editPodScenario (isNewScenario, index) {
      this.modalOptions.isCreatingPodScenario = isNewScenario
      if (isNewScenario) {
        this.$refs.podScenarioModal.openModal(PodScenarioModal.DEFAULT_POD_SCENARIO)
      } else {
        this.modalOptions.selectedPodScenarioIndex = index
        this.$refs.podScenarioModal.openModal(this.mutableConfig.podScenarios[index])
      }
    },
    deletePodScenario (index) {
      this.$delete(this.mutableConfig.podScenarios, index)
    }
  },
  data () {
    return {
      constants,
      isSaveButtonDisabled: false,
      tableFields: {
        nodeScenario: [
          {key: 'name', label: 'Name'},
          {key: 'actions', label: 'Actions'}
        ],
        podScenario: [
          {key: 'name', label: 'Name'},
          {key: 'actions', label: 'Actions'}
        ],
        filters: [
          {key: 'name', label: 'Property Name'},
          {key: 'value', label: 'Property Value'},
          {key: 'actions', label: 'Actions'}
        ],
        actions: [
          {key: 'type', label: 'Type'},
          {key: 'params', label: 'Parameters'},
          {key: 'actions', label: 'Actions'}
        ]
      },
      formOptions: {
        randomSample: [
          {text: 'Disabled', value: constants.RANDOM_SAMPLE.DISABLED},
          {text: 'Size', value: constants.RANDOM_SAMPLE.SIZE},
          {text: 'Ratio', value: constants.RANDOM_SAMPLE.RATIO}
        ]
      },
      modalOptions: {
        selectedNodeScenarioIndex: -1,
        isCreatingNodeScenario: false
      },
      // Set when configuration modal is hidden, used to determine whether 'ok'
      // trigger was used after the modal has finished hiding (so it is safe to
      // open another modal). Required as only the $hide event has the trigger
      // but the hidden event does not.
      configurationModalHiddenTrigger: ''
    }
  },
  computed: {
    mutableConfig: {
      get () {
        return this.$store.state.configuration.mutableConfig
      },
      set (value) {
        this.$store.commit('updateMutableConfig', value)
      }
    },
    ...mapState({
      isPolicyLoaded: state => state.configuration.isPolicyLoaded,
      policyYaml: state => state.configuration.policyYaml
    })
  },
  created () {
    this.$store.dispatch('updatePolicy')
  }
}
</script>
