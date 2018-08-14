import Vue from 'vue'
import constants from '../constants.js'
import axios from 'axios'

export default {
  state: {
    isNodesLoaded: false,
    isPodsLoaded: false,
    nodes: [],
    // Object of booleans for each node where key is ID set to true if a node is changing
    isNodesChanging: {},
    pods: [],
    // Object of booleans for each pod, set to true if a pod is stopping
    isPodsStopping: {}
  },
  mutations: {
    setIsNodesLoaded (state, status) {
      state.isNodesLoaded = status
    },
    setIsPodsLoaded (state, status) {
      state.isPodsLoaded = status
    },
    setNodes (state, nodes) {
      // Add a property which allow a row in state.nodes to be mutated when a function
      // only has knowledge of the contents of a single row
      state.nodes = nodes.map((nodes, idx) => {
        nodes._idInNodesArray = idx
        return nodes
      })

      state.isNodesChanging = nodes.map(() => false)
    },
    setPods (state, pods) {
      // Add a property which allow a row in state.pods to be mutated when a function
      // only has knowledge of the contents of a single row
      state.pods = pods.map((pods, idx) => {
        pods._idInPodsArray = idx
        return pods
      })

      state.isPodsStopping = pods.map(() => false)
    },
    setNodeStatus (state, {index, status}) {
      Vue.set(state.node[index], 'state', status)
    },
    setIsNodeChanging (state, {index, isChanging}) {
      Vue.set(state.isNodesChanging, index, isChanging)
    },
    setIsPodStopping (state, {index, isStopping}) {
      Vue.set(state.isPodsStopping, index, isStopping)
    }
  },
  actions: {
    async updateNodes ({commit}) {
      commit('setIsNodesLoaded', false)
      try {
        let response = await axios.get(Vue.prototype.$config['baseUrl'] + '/nodes')
        commit('setNodes', response.data['nodes'])
      } catch (err) {
        console.error('Unable to retrieve nodes\n' + err)
      }
      commit('setIsNodesLoaded', true)
    },
    async updatePods ({commit}, namespace = '') {
      commit('setIsPodsLoaded', false)
      try {
        let response = await axios.get(Vue.prototype.$config['baseUrl'] + '/pods?namespace=' + namespace)
        commit('setPods', response.data['pods'])
      } catch (err) {
        console.error('Unable to retrieve pods\n' + err)
      }
      commit('setIsPodsLoaded', true)
    },
    async startNode ({commit, state}, index) {
      commit('setIsNodeChanging', {index, isChanging: true})
      try {
        await axios.post(Vue.prototype.$config['baseUrl'] + '/nodes', {
          'action': 'start',
          'ip': state.nodes[index]['ip']
        })
        commit('setNodeStatus', index, constants.NODE_STATES.UP)
      } catch (err) {
        console.error('Unable to start node\n' + err)
        throw err
      }
      commit('setIsNodeChanging', {index, isChanging: false})
    },
    async stopNode ({commit, state}, index) {
      commit('setIsNodeChanging', {index, isChanging: true})
      try {
        await axios.post(Vue.prototype.$config['baseUrl'] + '/nodes', {
          'action': 'stop',
          'ip': state.nodes[index]['ip']
        })
        commit('setNodeStatus', index, constants.NODE_STATES.DOWN)
      } catch (err) {
        console.error('Unable to stop node\n' + err)
        throw err
      }
      commit('setIsNodeChanging', {index, isChanging: false})
    },
    async killPod ({commit, state}, index, isForced) {
      commit('setIsPodStopping', {index, isStopping: true})
      try {
        await axios.post(Vue.prototype.$config['baseUrl'] + '/pods', {
          'isForced': isForced,
          'uid': state.pods[index]['uid']
        })
      } catch (err) {
        console.error('Unable to kill pod\n' + err)
        throw err
      }
      commit('setIsPodStopping', {index, isStopping: false})
    }
  }
}
