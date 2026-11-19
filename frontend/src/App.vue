<script setup>
import { onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearSession, session, sessionExpired } from './session'

const router = useRouter()
const route = useRoute()
let expirationTimer

watch(
  session,
  (value) => {
    clearTimeout(expirationTimer)
    if (value) {
      expirationTimer = setTimeout(
        () => clearSession(true),
        Math.max(0, value.expiresAt - Date.now()),
      )
    } else if (route.meta.requiresAuth) {
      router.replace({
        name: 'login',
        query: { redirect: route.fullPath, ...(sessionExpired.value ? { expired: '1' } : {}) },
      })
    }
  },
  { immediate: true },
)

onUnmounted(() => clearTimeout(expirationTimer))
</script>

<template>
  <RouterView />
</template>
