import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import BootstrapVue from 'bootstrap-vue'
import '../scss/style.scss'
import VueHighlightJS from 'vue-highlightjs'
import {library} from '@fortawesome/fontawesome-svg-core'
import {faSpinner, faSync, faRobot, faAlignJustify, faCog, faServer, faDatabase} from '@fortawesome/free-solid-svg-icons'
import {FontAwesomeIcon} from '@fortawesome/vue-fontawesome'

library.add(faSpinner, faSync, faRobot, faAlignJustify, faCog, faServer, faDatabase)
Vue.component('font-awesome-icon', FontAwesomeIcon)

Vue.use(BootstrapVue)
Vue.use(VueHighlightJS)

Vue.config.productionTip = false

// Retrieve custom variables from the DOM, overriding the default configuration
// if a JSON object under ID 'config' is present
let config = {
  'baseUrl': 'http://localhost:9090/api'
}

const baseUrlInput = document.getElementById('baseUrl')
if (baseUrlInput !== null && baseUrlInput.value !== '{{ baseUrl }}') {
  config.baseUrl = baseUrlInput.value
}

Vue.prototype.$config = config

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
