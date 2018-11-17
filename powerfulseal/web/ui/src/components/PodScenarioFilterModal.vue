<!--
PodScenarioFilterModal is a component used for *editing* filters. The model
is to be opened from a PodScenarioModal.

The modal is opened and the filter to be edited is loaded in by calling
`openModal(filter)`.

If the user clicks "OK" (to save), the "updated" key is emitted, with the single
parameter being the modified filter.

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
            <h2>Filter</h2>
        </div>

        <b-form-group horizontal
                      :label-cols="2"
                      breakpoint="md"
                      label="Name"
                      label-for="name">
            <b-form-input id="name"
                          type="text"
                          v-model="filter.name"
                          placeholder="">
            </b-form-input>
        </b-form-group>
        <b-form-group horizontal
                      :label-cols="2"
                      breakpoint="md"
                      label="Value"
                      label-for="value">
            <b-form-input id="value"
                          type="text"
                          v-model="filter.value"
                          placeholder="">
            </b-form-input>
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

const DEFAULT_FILTER = {
  name: '',
  value: ''
}

export default {
  name: 'pod-scenario-filter-modal',
  data () {
    return {
      constants,
      filter: DEFAULT_FILTER
    }
  },
  methods: {
    openModal (filter) {
      this.filter = _.cloneDeep(filter)
      this.$refs.modal.show()
    },
    handleSave (evt) {
      this.$emit('updated', this.filter)
      this.$refs.modal.hide()
    },
    handleDiscard (evt) {
      this.$refs.modal.hide()
    },
    handleHidden () {
      this.$emit('hidden')
    }
  }
}
</script>
