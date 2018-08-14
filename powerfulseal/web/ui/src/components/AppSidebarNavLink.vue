<template>
    <b-link v-if="isRealLink" :href="url" class="nav-link">
        {{ name }}
    </b-link>
    <router-link v-else :to="url" class="nav-link">
        {{name}}
        <b-badge :variant="badge.variant">{{badge.text}}</b-badge>
    </router-link>
</template>

<script>
export default {
  name: 'app-sidebar-nav-link',
  props: {
    name: {
      type: String,
      default: ''
    },
    url: {
      type: String,
      default: ''
    },
    badge: {
      default: ''
    }

  },

  computed: {
    isRealLink: function () {
      return (this.url || '').startsWith('http')
    }
  }
}
</script>
