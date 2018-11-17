<template>
    <header class="app-header navbar">
        <b-link class="navbar-brand" to="/#/">PowerfulSeal</b-link>
        <button class="navbar-toggler sidebar-toggler d-md-down-none" type="button" @click="sidebarToggle">&#9776;</button>
        <button class="navbar-toggler mobile-sidebar-toggler d-lg-none" type="button" @click="mobileSidebarToggle">&#9776;</button>
    </header>
</template>

<script>
export default {
  name: 'app-header',
  methods: {
    sidebarToggle (e) {
      e.preventDefault()
      document.body.classList.toggle('sidebar-hidden')
    },
    sidebarMinimize (e) {
      e.preventDefault()
      document.body.classList.toggle('sidebar-minimized')
    },
    mobileSidebarToggle (e) {
      e.preventDefault()
      document.body.classList.toggle('sidebar-mobile-show')
    },
    asideToggle (e) {
      e.preventDefault()
      document.body.classList.toggle('aside-menu-hidden')
    }
  }
}
</script>
