import Vue from 'vue'
import Vuex from 'vuex'
import dashboard from './store/dashboard.js'
import configuration from './store/configuration.js'
import items from './store/items.js'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    dashboard,
    configuration,
    items
  }
})
