<!--
PodScenarioModal is a component used for *adding new and editing* pod
scenarios. The model is to be opened from the configuration page.

# Modal

The modal is opened and the scenario to be edited is loaded in by calling
`openModal(scenario)`. When creating a modal, you may pass in DEFAULT_POD_SCENARIO.
If the user clicks "OK" (to save), the "updated" key is emitted, with the single
parameter being the modified scenario.

# Sub-modals

This modal has three sub-modals (matcher, filter and actions) for the purpose of
either editing/creating these objects. The reason why modals are opened instead
of input boxes replacing a table row in-place is because some tables include
columns of arrays (which would be represented by a further table).

The lifecycle of a sub-modal is as follows:
1. The current modal is hidden before opening the sub-modal (to prevent errors
caused by contention for the modal manager)
2. The user either clicks Discard/Save in the sub-modal after making changes,
optionally emitting `updated` with the updated object
3. The sub-modal is hidden, emitting `hidden`
4. The modal listens to `hidden` (handleSubModalHidden()) so that it knows when
to show itself (again to prevent contention over the modal manager)

# Ability to discard changes and relevance to deep cloning

The component intentionally deep clones the scenario which is passed in so that
the user is able to cancel/hide the modal without saving changes.
-->
<template>
    <div>
        <b-modal size="lg"
                 ref="modal"
                 :hide-header-close="true"
                 :noCloseOnBackdrop="true"
                 :noCloseOnEsc="true">
            <div slot="modal-header">
                <h1>Pod Scenario</h1>
            </div>

            <h2>General</h2>
            <b-form-group horizontal
                          :label-cols="2"
                          breakpoint="md"
                          label="Scenario Name"
                          label-for="podScenarioName">
                <b-form-input id="podScenarioName"
                              type="text"
                              v-model="modifiedScenario.name"
                              placeholder="">
                </b-form-input>
            </b-form-group>

            <b-form-group>
                <h2>Matchers</h2>
                <b-table :items="modifiedScenario.matchers"
                         :fields="tableFields.matchers">
                    <template slot="type" slot-scope="row">{{constants.POD_MATCHER_LABELS[row.value]}}</template>
                    <template slot="params" slot-scope="row">{{row.value | stringifyParams}}</template>
                    <template slot="actions" slot-scope="row">
                        <b-button size="sm"
                                  class="mr-1"
                                  variant="primary"
                                  @click.stop="editMatcher(false, row.index)">
                            Edit
                        </b-button>
                        <b-button size="sm"
                                  variant="danger"
                                  @click.stop="deleteMatcher(row.index)">
                            Delete
                        </b-button>
                    </template>
                </b-table>
                <b-button-group>
                    <b-button variant="primary"
                              @click.stop="editMatcher(true, -1)">
                        Add
                    </b-button>
                </b-button-group>
            </b-form-group>

            <b-form-group>
                <h2>Filters</h2>
                <b-table :items="modifiedScenario.filters"
                         :fields="tableFields.filters">
                    <template slot="name" slot-scope="row">{{row.value}}</template>
                    <template slot="value" slot-scope="row">{{row.value}}</template>
                    <template slot="actions" slot-scope="row">
                        <b-button size="sm"
                                  class="mr-1"
                                  variant="primary"
                                  @click.stop="editFilter(row.index)">
                            Edit
                        </b-button>
                        <b-button size="sm"
                                  variant="danger"
                                  @click.stop="deleteFilter(row.index)">
                            Delete
                        </b-button>
                    </template>
                </b-table>

                <b-form inline>
                    <label class="sr-only" for="filterPropertyName">Name</label>
                    <b-input class="mb-2 mr-sm-2 mb-sm-0"
                             id="filterPropertyName"
                             v-model="formFields.newFilterName"
                             placeholder="Property Name"></b-input>

                    <label class="sr-only" for="filterPropertyValue">Value</label>
                    <b-input class="mb-2 mr-sm-2 mb-sm-0"
                             id="filterPropertyValue"
                             v-model="formFields.newFilterValue"
                             placeholder="Property Value"></b-input>
                    <b-button variant="primary"
                              @click.stop="addFilter()">
                        Add
                    </b-button>
                </b-form>
            </b-form-group>

            <h4>Time of Execution</h4>
            <div class="form-row"></div>
            <b-form-checkbox id="isTimeOfExecutionEnabled"
                             v-model="modifiedScenario.isTimeOfExecutionEnabled"
                             :plain="true">
                Enabled
            </b-form-checkbox>

            <div v-if="modifiedScenario.isTimeOfExecutionEnabled">
                <b-form-group horizontal
                              :label-cols="2"
                              breakpoint="md"
                              label="Days of Week"
                              label-for="daysOfWeek">
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.monday"
                                     :plain="true">
                        Monday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.tuesday"
                                     :plain="true">
                        Tuesday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.wednesday"
                                     :plain="true">
                        Wednesday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.thursday"
                                     :plain="true">
                        Thursday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.friday"
                                     :plain="true">
                        Friday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.saturday"
                                     :plain="true">
                        Saturday
                    </b-form-checkbox>
                    <b-form-checkbox v-model="modifiedScenario.dayOfWeek.sunday"
                                     :plain="true">
                        Sunday
                    </b-form-checkbox>
                </b-form-group>

                <b-form-group horizontal
                              :label-cols="2"
                              breakpoint="md"
                              label="Start time">
                    <b-form inline>
                        <label class="sr-only" for="startTimeHour">Start Time Hour</label>
                        <b-input class="mb-2 mr-1 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="24"
                                 id="startTimeHour"
                                 v-model.number="modifiedScenario.startTime.hour">
                        </b-input>
                        :

                        <label class="sr-only" for="startTimeMinute">Start Time Minute</label>
                        <b-input class="mb-2 ml-1 mr-1 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="60"
                                 id="startTimeMinute"
                                 v-model.number="modifiedScenario.startTime.minute">
                        </b-input>
                        :

                        <label class="sr-only" for="startTimeSecond">Start Time Second</label>
                        <b-input class="mb-2 ml-1 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="60"
                                 id="startTimeSecond"
                                 v-model.number="modifiedScenario.startTime.second">
                        </b-input>
                    </b-form>
                </b-form-group>

                <b-form-group horizontal
                              :label-cols="2"
                              breakpoint="md"
                              label="End time">
                    <b-form inline>
                        <label class="sr-only" for="endTimeHour">End Time Hour</label>
                        <b-input class="mb-2 mr-1 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="24"
                                 id="endTimeHour"
                                 v-model.number="modifiedScenario.endTime.hour">
                        </b-input>
                        :
                        <label class="sr-only" for="endTimeMinute">End Time Minute</label>
                        <b-input class="mb-2 ml-1 mr-1 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="60"
                                 id="endTimeMinute"
                                 v-model.number="modifiedScenario.endTime.minute">
                        </b-input>
                        :
                        <label class="sr-only" for="endTimeSecond">End Time Second</label>
                        <b-input class="mb-2 ml-1 mr-0 mb-sm-0"
                                 type="number"
                                 min="0"
                                 max="60"
                                 id="endTimeSecond"
                                 v-model.number="modifiedScenario.endTime.second">
                        </b-input>
                    </b-form>
                </b-form-group>
            </div>

            <h4>Random Sample</h4>

            <b-form-radio-group :plain="true"
                                v-model.number="modifiedScenario.randomSample.type"
                                :options="formOptions.randomSample">
            </b-form-radio-group>

            <b-form-group horizontal
                          :label-cols="2"
                          breakpoint="md"
                          label="Size"
                          label-for="randomSampleSize"
                          v-if="modifiedScenario.randomSample.type === constants.RANDOM_SAMPLE.SIZE">
                <b-input class="mb-2 mr-sm-2 mb-sm-0"
                         type="number"
                         id="randomSampleSize"
                         v-model.number="modifiedScenario.randomSample.size"></b-input>
            </b-form-group>

            <b-form-group horizontal
                          :label-cols="2"
                          breakpoint="md"
                          label="Ratio"
                          label-for="randomSampleRatio"
                          v-if="modifiedScenario.randomSample.type === constants.RANDOM_SAMPLE.RATIO">
                <b-input class="mb-2 mr-sm-2 mb-sm-0"
                         type="number"
                         step="0.05"
                         id="randomSampleRatio"
                         v-model.number="modifiedScenario.randomSample.ratio"></b-input>
            </b-form-group>

            <h4>Probability Pass All</h4>

            <b-form-checkbox id="isProbabilityPassAllEnabled"
                             v-model="modifiedScenario.probabilityPassAll.isEnabled"
                             :plain="true">
                Enabled
            </b-form-checkbox>

            <b-form-group horizontal
                          :label-cols="2"
                          breakpoint="md"
                          label="Probability"
                          label-for="probabilityPassAll"
                          v-if="modifiedScenario.probabilityPassAll.isEnabled">
                <b-input class="mb-2 mr-sm-2 mb-sm-0"
                         type="number"
                         step="0.05"
                         id="probabilityPassAll"
                         v-model.number="modifiedScenario.probabilityPassAll.probability"></b-input>
            </b-form-group>

            <h4>Actions</h4>
            <b-table :items="modifiedScenario.actions"
                     :fields="tableFields.actions">
                <template slot="type" slot-scope="row">{{constants.POD_ACTION_TYPE_LABELS[row.value]}}</template>
                <template slot="params" slot-scope="row">{{row.value | stringifyParams}}</template>
                <template slot="actions" slot-scope="row">
                    <b-button size="sm"
                              class="mr-1"
                              variant="primary"
                              @click.stop="editAction(false, row.index)">
                        Edit
                    </b-button>
                    <b-button size="sm"
                              variant="danger"
                              @click.stop="deleteAction(row.index)">
                        Delete
                    </b-button>
                </template>
            </b-table>
            <b-button-group>
                <b-button variant="primary"
                          @click.stop="editAction(true, -1)">
                    Add
                </b-button>
            </b-button-group>

            <div slot="modal-footer">
                <button @click="handleDiscard"
                        type="button"
                        class="btn btn-secondary mr-1">
                    Discard
                </button>
                <button @click="handleSave"
                        type="button"
                        class="btn btn-primary">
                    Save
                </button>
            </div>
        </b-modal>
        <pod-scenario-matcher-modal ref="podScenarioMatcherModal"
                                    @hidden="handleSubModalHidden"
                                    @updated="handleMatcherUpdated"/>
        <pod-scenario-filter-modal ref="podScenarioFilterModal"
                                   @hidden="handleSubModalHidden"
                                   @updated="handleFilterUpdated"/>
        <pod-scenario-action-modal ref="podScenarioActionModal"
                                   @hidden="handleSubModalHidden"
                                   @updated="handleActionUpdated"/>
    </div>
</template>

<script>
import constants from '../constants.js'
import _ from 'lodash'
import PodScenarioMatcherModal from './PodScenarioMatcherModal'
import PodScenarioFilterModal from './PodScenarioFilterModal'
import PodScenarioActionModal from './PodScenarioActionModal'
import Vue from 'vue'

const DEFAULT_POD_SCENARIO = {
  name: '',
  matchers: [],
  filters: [],
  isTimeOfExecutionEnabled: false,
  dayOfWeek: {
    monday: true,
    tuesday: true,
    wednesday: true,
    thursday: true,
    friday: true,
    saturday: false,
    sunday: false
  },
  startTime: {
    hour: 10,
    minute: 0,
    second: 0
  },
  endTime: {
    hour: 17,
    minute: 30,
    second: 0
  },
  randomSample: {
    type: constants.RANDOM_SAMPLE.DISABLED,
    size: 5,
    ratio: 0.2
  },
  probabilityPassAll: {
    isEnabled: false,
    probability: 0.5
  },
  actions: []
}

export default {
  components: {
    PodScenarioMatcherModal,
    PodScenarioFilterModal,
    PodScenarioActionModal
  },
  DEFAULT_POD_SCENARIO,
  name: 'pod-scenario-modal',
  data () {
    return {
      constants,
      modifiedScenario: _.cloneDeep(DEFAULT_POD_SCENARIO),
      tableFields: {
        matchers: [
          {key: 'type', label: 'Type'},
          {key: 'params', label: 'Parameters'},
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
      formFields: {
        newMatcherName: '',
        newMatcherValue: '',
        newFilterName: '',
        newFilterValue: ''
      },
      formOptions: {
        randomSample: [
          {text: 'Disabled', value: constants.RANDOM_SAMPLE.DISABLED},
          {text: 'Size', value: constants.RANDOM_SAMPLE.SIZE},
          {text: 'Ratio', value: constants.RANDOM_SAMPLE.RATIO}
        ]
      },
      modalOptions: {
        selectedMatcherIndex: -1,
        selectedFilterIndex: -1,
        selectedActionIndex: -1,
        isCreatingMatcher: false,
        isCreatingAction: false
      }
    }
  },
  filters: {
    stringifyParams (params) {
      return params.map(row => row.name + ': ' + row.value).join(' | ')
    }
  },
  methods: {
    /* Modal methods */
    openModal (scenario) {
      this.modifiedScenario = _.cloneDeep(scenario)
      this.$refs.modal.show()
    },
    handleSave (evt) {
      this.$emit('updated', this.modifiedScenario)
      this.$refs.modal.hide()
    },
    handleDiscard (evt) {
      this.$refs.modal.hide()
    },
    handleSubModalHidden () {
      this.$refs.modal.show()
    },
    /* Matcher sub-modal methods */
    handleMatcherUpdated (matcher) {
      if (this.modalOptions.isCreatingMatcher) {
        this.modifiedScenario.matchers.push(matcher)
      } else {
        Object.keys(this.modifiedScenario.matchers[this.modalOptions.selectedMatcherIndex]).forEach(key => {
          Vue.set(this.modifiedScenario.matchers[this.modalOptions.selectedMatcherIndex], key, matcher[key])
        })
      }
    },
    editMatcher (isNewMatcher, index) {
      this.modalOptions.isCreatingMatcher = isNewMatcher
      if (isNewMatcher) {
        this.$refs.podScenarioMatcherModal.openModal(PodScenarioMatcherModal.DEFAULT_MATCHER)
      } else {
        this.modalOptions.selectedMatcherIndex = index
        this.$refs.podScenarioMatcherModal.openModal(this.modifiedScenario.matchers[index])
      }
    },
    deleteMatcher (index) {
      this.$delete(this.modifiedScenario.matchers, index)
    },
    /* Filter sub-modal methods */
    handleFilterUpdated (filter) {
      Object.keys(this.modifiedScenario.filters[this.modalOptions.selectedFilterIndex]).forEach(key => {
        Vue.set(this.modifiedScenario.filters[this.modalOptions.selectedFilterIndex], key, filter[key])
      })
    },
    addFilter () {
      this.modifiedScenario.filters.push({
        name: this.formFields.newFilterName,
        value: this.formFields.newFilterValue
      })

      this.formFields.newFilterName = ''
      this.formFields.newFilterValue = ''
    },
    editFilter (index) {
      this.$refs.modal.hide()
      this.modalOptions.selectedFilterIndex = index
      this.$refs.podScenarioFilterModal.openModal(this.modifiedScenario.filters[index])
    },
    deleteFilter (index) {
      this.$delete(this.modifiedScenario.filters, index)
    },
    /* Action sub-modal methods */
    handleActionUpdated (action) {
      if (this.modalOptions.isCreatingAction) {
        this.modifiedScenario.actions.push(action)
      } else {
        Object.keys(this.modifiedScenario.actions[this.modalOptions.selectedActionIndex]).forEach(key => {
          Vue.set(this.modifiedScenario.actions[this.modalOptions.selectedActionIndex], key, action[key])
        })
      }
    },
    editAction (isNewAction, index) {
      this.modalOptions.isCreatingAction = isNewAction
      if (isNewAction) {
        this.$refs.podScenarioActionModal.openModal(PodScenarioActionModal.DEFAULT_ACTION)
      } else {
        this.modalOptions.selectedActionIndex = index
        this.$refs.podScenarioActionModal.openModal(this.modifiedScenario.actions[index])
      }
    },
    deleteAction (index) {
      this.$delete(this.modifiedScenario.actions, index)
    }
  }
}
</script>
