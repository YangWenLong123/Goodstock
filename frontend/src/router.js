import { createRouter, createWebHistory } from 'vue-router'
import { clearSession, session } from './session'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('./views/LoginView.vue'),
    },
    {
      path: '/',
      name: 'products',
      component: () => import('./views/ProductsView.vue'),
      meta: { requiresAuth: true },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  if (session.value && session.value.expiresAt <= Date.now()) clearSession(true)
  if (to.meta.requiresAuth && !session.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && session.value) return { name: 'products' }
})

export default router
