<!--
PodScenarioActionModal is a component used for *editing* actions. The model
is to be opened from a PodScenarioModal.

The modal is opened and the action to be edited is loaded in by calling
`openModal(action)`.

If the user clicks "OK" (to save), the "updated" key is emitted, with the single
parameter being the modified action.

The component intentionally deep clones the scenario which is passed in so that
the user is able to cancel/hide the modal without saving changes.
-->
<template>
    <b-modal size="lg"
             ref="modal"
             @hidden="handleHidden"
             :hide-header-close="true"
             :noCloseOnBackdrop="true"
             :noCloseOnEsc="true">
        <div slot="modal-header">
            <h2>Action</h2>
        </div>

        <b-form-group horizontal
                      :label-cols="2"
                      breakpoint="md"
                      label="Type"
                      label-for="type">
            <b-form-select v-model="action.type"
                           :options="options">
            </b-form-select>
        </b-form-group>
        <b-form-group horizontal
                      :label-cols="2"
                      breakpoint="md"
                      label="Parameters"
                      label-for="params">
            <b-table id="params"
                     :items="action.params"
                     :fields="tableFields">
                <template slot="name" slot-scope="row">{{row.value}}</template>
                <template slot="value" slot-scope="row">{{row.value}}</template>
                <template slot="actions" slot-scope="row">
                    <b-button size="sm"
                              class="mr-1"
                              variant="primary"
                              @click.stop="deleteParam(row.index)">
                        Delete
                    </b-button>
                </template>
            </b-table>

            <b-form inline>
                <label class="sr-only" for="parameterName">Name</label>
                <b-input class="mb-2 mr-sm-2 mb-sm-0"
                         id="parameterName"
                         v-model="newParameterName"
                         placeholder="Property Name"></b-input>

                <label class="sr-only" for="parameterValue">Value</label>
                <b-input class="mb-2 mr-sm-2 mb-sm-0"
                         id="parameterName"
                         v-model="newParameterValue"
                         placeholder="Property Value"></b-input>
                <b-button variant="primary"
                          @click.stop="addParam()">
                    Add
                </b-button>
            </b-form>
        </b-form-group>
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
</template>

<script>
import constants from '../constants.js'
import _ from 'lodash'

const DEFAULT_ACTION = {
  type: 0,
  params: []
}

export default {
  DEFAULT_ACTION,
  name: 'pod-scenario-action-modal',
  data () {
    return {
      action: DEFAULT_ACTION,
      tableFields: [
        {key: 'name', label: 'Parameter Name'},
        {key: 'value', label: 'Parameter Value'},
        {key: 'actions', label: 'Actions'}
      ],
      newParameterName: '',
      newParameterValue: ''
    }
  },
  computed: {
    options () {
      return Object.keys(constants.POD_ACTION_TYPES).map(key => {
        let index = constants.POD_ACTION_TYPES[key]
        let text = constants.POD_ACTION_TYPE_LABELS[index]
        return {value: index, text: text}
      })
    }
  },
  methods: {
    openModal (action) {
      this.action = _.cloneDeep(action)
      this.$refs.modal.show()
    },
    handleSave () {
      this.$emit('updated', this.action)
      this.$refs.modal.hide()
    },
    handleDiscard () {
      this.$refs.modal.hide()
    },
    handleHidden () {
      this.$emit('hidden')
    },
    addParam () {
      this.action.params.push({
        name: this.newParameterName,
        value: this.newParameterValue
      })

      this.newParameterName = ''
      this.newParameterValue = ''
    },
    deleteParam (index) {
      this.$delete(this.action.params, index)
    }
  }
}
</script>
