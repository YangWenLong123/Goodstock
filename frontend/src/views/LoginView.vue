<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  LockKeyhole,
  Package,
  ShieldCheck,
  UserRound,
} from 'lucide-vue-next'
import BrandMark from '../components/BrandMark.vue'
import { authApi } from '../api'
import { saveSession } from '../session'

const router = useRouter()
const route = useRoute()
const username = ref('')
const password = ref('')
const showPassword = ref(false)
const busy = ref(false)
const error = ref('')

async function login() {
  if (busy.value) return
  error.value = ''
  busy.value = true
  try {
    saveSession(await authApi.login(username.value.trim(), password.value))
    const redirect = route.query.redirect
    await router.replace(
      typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
        ? redirect
        : '/',
    )
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="login-layout">
    <section class="login-story">
      <BrandMark />
      <div class="story-content">
        <span class="eyebrow"><span class="tiny-dot" /> A LITTLE ORDER. A LOT OF POSSIBILITY.</span>
        <h1>让商品管理，<br />回归简单<span>。</span></h1>
        <p class="story-description">
          从第一件商品到每一次上新，<br />把繁琐留给系统，把专注留给生意。
        </p>
        <div class="inventory-illustration" aria-hidden="true">
          <div class="illustration-grid" />
          <div class="illustration-package package-back">
            <Package :size="70" :stroke-width="1" />
          </div>
          <div class="illustration-package package-front">
            <Package :size="100" :stroke-width="1" />
          </div>
          <div class="illustration-badge">
            <span><Check :size="13" /></span> 一切，井然有序
          </div>
          <span class="illustration-caption">YOUR INVENTORY, IN GOOD HANDS.</span>
        </div>
      </div>
      <div class="story-footer"><span>为每一份认真经营而设计</span><span>EST. 2026</span></div>
    </section>

    <section class="login-form-side">
      <div class="mobile-login-brand"><BrandMark /></div>
      <div class="login-form-wrap">
        <span class="section-kicker">WELCOME BACK</span>
        <h2>欢迎回来</h2>
        <p class="login-subtitle">登录你的工作台，开始有条不紊的一天。</p>
        <div v-if="route.query.expired" class="notice">登录状态已失效，请重新登录。</div>
        <form class="login-form" @submit.prevent="login">
          <label class="field-label" for="username">用户名</label>
          <div class="input-with-icon">
            <UserRound :size="18" /><input
              id="username"
              v-model="username"
              name="username"
              autocomplete="username"
              placeholder="请输入用户名"
              maxlength="50"
              required
              autofocus
              :disabled="busy"
            />
          </div>
          <label class="field-label" for="password">密码</label>
          <div class="input-with-icon">
            <LockKeyhole :size="18" /><input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              name="password"
              autocomplete="current-password"
              placeholder="请输入登录密码"
              required
              :disabled="busy"
            /><button
              class="password-toggle"
              type="button"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <component :is="showPassword ? EyeOff : Eye" :size="18" />
            </button>
          </div>
          <p v-if="error" class="form-error" role="alert">{{ error }}</p>
          <button class="button button-primary login-submit" type="submit" :disabled="busy">
            <span v-if="busy" class="spinner" /><span>{{ busy ? '正在登录…' : '登录工作台' }}</span
            ><ArrowRight v-if="!busy" :size="18" />
          </button>
        </form>
        <div class="demo-credentials">
          <span class="demo-label">演示账号</span>
          <p>
            用户名 <code>admin</code><span class="credential-divider" />密码
            <code>Admin@123456</code>
          </p>
        </div>
        <p class="secure-note"><ShieldCheck :size="15" /> 使用安全身份验证，安心管理每一件商品</p>
      </div>
      <footer class="login-copyright">© 2026 Goodstock. 用心管理，每一份好物。</footer>
    </section>
  </main>
</template>
