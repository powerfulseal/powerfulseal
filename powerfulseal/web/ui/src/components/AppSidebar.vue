<template>
    <div class="sidebar">
        <nav class="sidebar-nav">
            <div slot="header"></div>
            <ul class="nav">
                <li class="nav-item" v-for="(item, index) in navItems" :key="index">
                    <div v-if="item.title">
                        <app-sidebar-nav-title :name="item.name" :classes="item.class" :wrapper="item.wrapper"/>
                    </div>
                    <div v-else-if="item.divider">
                <li class="divider"></li>
    </div>
    <div v-else>
        <div v-if="item.children">
            <app-sidebar-nav-dropdown :name="item.name" :url="item.url" :icon="item.icon">
                <div v-for="(child, index) in item.children" :key="index">
                    <div v-if="child.children">
                        <app-sidebar-nav-dropdown :name="child.name" :url="child.url" :icon="child.icon">
                            <li class="nav-item" v-for="(child, index) in item.children" :key="index">
                                <app-sidebar-nav-link :name="child.name" :url="child.url" :icon="child.icon" :badge="child.badge"/>
                            </li>
                        </app-sidebar-nav-dropdown>
                    </div>
                    <div v-else>
                        <li class="nav-item">
                            <app-sidebar-nav-link :name="child.name" :url="child.url" :icon="child.icon" :badge="child.badge"/>
                        </li>
                    </div>
                </div>
            </app-sidebar-nav-dropdown>
        </div>
        <div v-else>
            <app-sidebar-nav-link :name="item.name" :url="item.url" :icon="item.icon" :badge="item.badge"/>
        </div>
    </div>
    </li>
    </ul>
    <slot></slot>
    <div slot="footer"></div>
    </nav>
    </div>
</template>

<style lang="css">
.nav-link {
    cursor: pointer;
}
</style>

<script>
import AppSidebarNavDropdown from './AppSidebarNavDropdown.vue'
import AppSidebarNavLink from './AppSidebarNavLink.vue'
import AppSidebarNavTitle from './AppSidebarNavTitle.vue'

export default {
  name: 'app-sidebar',
  props: {
    navItems: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  components: {
    'app-sidebar-nav-dropdown': AppSidebarNavDropdown,
    'app-sidebar-nav-link': AppSidebarNavLink,
    'app-sidebar-nav-title': AppSidebarNavTitle
  },
  methods: {
    handleClick (e) {
      e.preventDefault()
      e.target.parentElement.classList.toggle('open')
    }
  }
}
</script>
