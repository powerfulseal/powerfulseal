import Vue from 'vue'
import Router from 'vue-router'
import DashboardPage from './components/DashboardPage.vue'
import ConfigurationPage from './components/ConfigurationPage.vue'
import ItemsPage from './components/ItemsPage.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: DashboardPage
    },
    {
      path: '/configuration',
      name: 'Configuration',
      component: ConfigurationPage
    },
    {
      path: '/items',
      name: 'Nodes & Pods',
      component: ItemsPage
    }
  ]
})
