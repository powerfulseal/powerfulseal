import Vue from 'vue'
import axios from 'axios'
import _ from 'lodash'

export default {
  state: {
    isPolicyLoaded: false,
    // originalConfig stores the same configuration which is present on the web
    // server, while mutableConfig stores the configuration which is modified
    // by the the configuration form.
    policyYaml: '',
    originalConfig: {
      minSecondsBetweenRuns: 0,
      maxSecondsBetweenRuns: 300,
      nodeScenarios: [],
      podScenarios: []
    },
    mutableConfig: {
      // Seconds Between Runs
      minSecondsBetweenRuns: 0,
      maxSecondsBetweenRuns: 300,
      // Node Scenarios
      nodeScenarios: [],
      // Pod Scenarios
      podScenarios: []
    }
  },
  mutations: {
    setPolicy (state, policy) {
      state.originalConfig = _.cloneDeep(policy)
      state.mutableConfig = _.cloneDeep(policy)
    },
    setIsPolicyLoaded (state, status) {
      state.isPolicyLoaded = status
    },
    setPolicyYaml (state, policyYaml) {
      state.policyYaml = policyYaml
    },
    updateMutableConfig (state, value) {
      Object.keys(state.mutableConfig).forEach(key => {
        Vue.set(state.mutableConfig, key, value[key])
      })
    },
    resetMutableConfig (state) {
      state.mutableConfig = _.cloneDeep(state.originalConfig)
    }
  },
  actions: {
    async updatePolicy ({commit}) {
      commit('setIsPolicyLoaded', false)
      try {
        const response = await axios.get(Vue.prototype.$config['baseUrl'] + '/policy')
        commit('setPolicy', response.data)
      } catch (err) {
        console.error('Unable to retrieve policy\n' + err)
      }
      commit('setIsPolicyLoaded', true)
    },
    async saveConfig ({commit}, config) {
      try {
        await axios.put(Vue.prototype.$config['baseUrl'] + '/policy', {
          'policy': config
        })
        commit('setPolicy', config)
      } catch (err) {
        console.error('Unable to overwrite policy\n' + err)
        throw err
      }
    },
    async exportYaml ({commit}, policy) {
      try {
        const response = await axios.post(Vue.prototype.$config['baseUrl'] + '/policy', {
          'policy': policy
        })
        commit('setPolicyYaml', response.data['policy'])
      } catch (err) {
        console.error('Unable to export policy to YAML\n' + err)
        throw err
      }
    }
  }
}
