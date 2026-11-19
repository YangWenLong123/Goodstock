<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import {
  AlertCircle,
  ArrowUpRight,
  Box,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Eye,
  LayoutGrid,
  LogOut,
  Menu,
  Package,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  ShoppingBag,
  SlidersHorizontal,
  Trash2,
  TrendingUp,
  Wallet,
  X,
} from 'lucide-vue-next'
import BrandMark from '../components/BrandMark.vue'
import BaseModal from '../components/BaseModal.vue'
import ProductAvatar from '../components/ProductAvatar.vue'
import ProductForm from '../components/ProductForm.vue'
import { authApi, productApi } from '../api'
import { clearSession, session } from '../session'

const categories = ['数码配件', '办公文具', '生活用品', '服饰箱包']
const products = ref([])
const total = ref(0)
const stats = ref(null)
const statsError = ref('')
const filters = reactive({
  q: '',
  category: '',
  status: '',
  page: 1,
  page_size: 8,
})
const searchText = ref('')
const loading = ref(true)
const error = ref('')
const sidebarOpen = ref(false)
const modal = ref(null)
const selected = ref(null)
const modalLoading = ref(false)
const saving = ref(false)
const modalError = ref('')
const toast = ref('')
const hasFilters = computed(() => Boolean(filters.q || filters.category || filters.status))
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / filters.page_size)))
const pageNumbers = computed(() => {
  const start = Math.max(1, Math.min(filters.page - 2, pageCount.value - 4))
  return Array.from({ length: Math.min(5, pageCount.value) }, (_, index) => start + index)
})
const money = (value) =>
  new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY' }).format(Number(value || 0))
const number = (value) => new Intl.NumberFormat('zh-CN').format(value ?? 0)
const date = (value) =>
  new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(`${value}Z`))
let listController
let searchTimer
let toastTimer
let disposed = false

function notify(message) {
  clearTimeout(toastTimer)
  toast.value = message
  toastTimer = setTimeout(() => {
    toast.value = ''
  }, 3500)
}

async function loadProducts() {
  listController?.abort()
  const controller = new AbortController()
  listController = controller
  loading.value = true
  error.value = ''
  try {
    const data = await productApi.list({ ...filters }, controller.signal)
    if (controller.signal.aborted) return
    products.value = data.items
    total.value = data.total
    if (filters.page > 1 && !data.items.length)
      filters.page = Math.max(1, Math.ceil(data.total / filters.page_size))
  } catch (err) {
    if (err.name !== 'AbortError') error.value = err.message
  } finally {
    if (listController === controller) loading.value = false
  }
}

async function loadStats() {
  statsError.value = ''
  try {
    stats.value = await productApi.stats()
  } catch (err) {
    stats.value = null
    statsError.value = err.message
  }
}

async function refresh() {
  await Promise.all([loadProducts(), loadStats()])
}

watch(searchText, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    filters.q = value.trim()
    filters.page = 1
  }, 300)
})
watch(
  () => [filters.category, filters.status, filters.page_size],
  () => {
    filters.page = 1
  },
  { flush: 'sync' },
)
watch(() => ({ ...filters }), loadProducts)

function resetFilters() {
  clearTimeout(searchTimer)
  searchText.value = ''
  Object.assign(filters, { q: '', category: '', status: '', page: 1 })
}

function openCreate() {
  selected.value = null
  modalError.value = ''
  modal.value = 'create'
}

async function openProduct(product, mode) {
  selected.value = product
  modalError.value = ''
  modal.value = mode
  if (mode === 'delete') return
  modalLoading.value = true
  try {
    selected.value = await productApi.get(product.id)
  } catch (err) {
    modalError.value = err.message
  } finally {
    modalLoading.value = false
  }
}

function closeModal() {
  if (!saving.value && !modalLoading.value) modal.value = null
}

async function saveProduct(body) {
  if (saving.value) return
  saving.value = true
  modalError.value = ''
  try {
    const editing = modal.value === 'edit'
    if (editing) await productApi.update(selected.value.id, body)
    else await productApi.create(body)
    modal.value = null
    notify(editing ? '商品信息已更新' : '新商品已添加')
    await refresh()
  } catch (err) {
    modalError.value = err.message
  } finally {
    saving.value = false
  }
}

async function deleteProduct() {
  if (saving.value) return
  saving.value = true
  modalError.value = ''
  try {
    await productApi.remove(selected.value.id)
    modal.value = null
    notify('商品已删除')
    await refresh()
  } catch (err) {
    modalError.value = err.message
  } finally {
    saving.value = false
  }
}

function logout() {
  clearSession()
}

onMounted(async () => {
  try {
    await authApi.me()
    if (!disposed) await refresh()
  } catch (err) {
    error.value = err.message
    loading.value = false
  }
})

onUnmounted(() => {
  disposed = true
  listController?.abort()
  clearTimeout(searchTimer)
  clearTimeout(toastTimer)
})
</script>

<template>
  <div class="workspace">
    <div v-if="sidebarOpen" class="sidebar-scrim" @click="sidebarOpen = false" />
    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <BrandMark />
      <div class="workspace-label">管理工作台 <span>WORKSPACE</span></div>
      <nav class="sidebar-nav" aria-label="主导航">
        <RouterLink to="/" class="nav-link" @click="sidebarOpen = false"
          ><LayoutGrid :size="19" /><span>商品管理</span><span class="nav-active-dot"
        /></RouterLink>
      </nav>
      <div class="sidebar-note">
        <span class="sidebar-note-icon"><Box :size="25" :stroke-width="1.3" /></span>
        <p>每一件好物，<br />都值得被好好管理。</p>
        <span>LESS MESS, MORE BUSINESS.</span>
      </div>
      <div class="sidebar-account">
        <div class="avatar">
          {{ session?.user?.display_name?.slice(0, 1) || '管' }}
        </div>
        <div class="account-text">
          <strong>{{ session?.user?.display_name }}</strong><span>工作台管理员</span>
        </div>
        <button class="icon-button" aria-label="退出登录" title="退出登录" @click="logout">
          <LogOut :size="17" />
        </button>
      </div>
    </aside>

    <div class="main-shell">
      <header class="topbar">
        <div class="breadcrumbs">
          <button class="icon-button mobile-menu" aria-label="打开导航" @click="sidebarOpen = true">
            <Menu :size="21" /></button
          ><span>工作台</span><ChevronRight :size="14" /><strong>商品管理</strong>
        </div>
        <span class="workspace-status"><span class="tiny-dot" /> 工作空间已就绪</span>
      </header>
      <main class="main-content">
        <div class="page-heading">
          <div>
            <span class="section-kicker">YOUR PRODUCTS, WELL ORGANIZED</span>
            <h1>商品管理<span class="heading-dot">.</span></h1>
            <p>掌握每一件商品，让日常经营更从容。</p>
          </div>
          <button class="button button-primary" @click="openCreate">
            <Plus :size="18" />新增商品
          </button>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-top">
              <span>商品总数</span><span class="stat-icon"><Package :size="19" /></span>
            </div>
            <div class="stat-value">
              {{ stats ? number(stats.total) : '—' }}<span v-if="stats">件</span>
            </div>
            <p>你的全部商品，一目了然</p>
          </div>
          <div class="stat-card">
            <div class="stat-top">
              <span>在售商品</span><span class="stat-icon green"><ShoppingBag :size="19" /></span>
            </div>
            <div class="stat-value">
              {{ stats ? number(stats.active) : '—' }}<span v-if="stats">件</span>
            </div>
            <p><span class="mini-dot green-dot" /> 正在销售中的好物</p>
          </div>
          <div class="stat-card">
            <div class="stat-top">
              <span>库存预警</span><span class="stat-icon amber"><TrendingUp :size="19" /></span>
            </div>
            <div class="stat-value" :class="{ 'amber-text': stats?.low_stock }">
              {{ stats ? number(stats.low_stock) : '—' }}<span v-if="stats">件</span>
            </div>
            <p>在售且库存 ≤ 10 件，记得补货</p>
          </div>
          <div class="stat-card">
            <div class="stat-top">
              <span>库存总值</span><span class="stat-icon"><Wallet :size="19" /></span>
            </div>
            <div class="stat-value stat-money">
              {{ stats ? money(stats.inventory_value) : '—' }}
            </div>
            <p>按全部商品售价 × 库存计算</p>
          </div>
        </div>
        <div v-if="statsError" class="inline-error" role="alert">
          <AlertCircle :size="16" /><span>统计加载失败：{{ statsError }}</span
          ><button class="text-button" @click="loadStats">重试</button>
        </div>

        <section class="product-panel" aria-labelledby="products-heading">
          <div class="panel-heading">
            <div class="panel-title">
              <h2 id="products-heading">商品列表</h2>
              <span class="count-badge">{{ total }} 件商品</span>
            </div>
            <button
              class="icon-button refresh-button"
              aria-label="刷新商品"
              title="刷新商品"
              :disabled="loading"
              @click="refresh"
            >
              <RefreshCw :size="17" :class="{ spinning: loading }" />
            </button>
          </div>
          <div class="table-toolbar">
            <div class="search-input">
              <Search :size="17" /><input
                v-model="searchText"
                aria-label="搜索商品名称或 SKU"
                placeholder="搜索商品名称、SKU…"
                maxlength="100"
              /><button
                v-if="searchText"
                class="icon-button"
                aria-label="清除搜索"
                @click="searchText = ''"
              >
                <X :size="14" />
              </button>
            </div>
            <div class="filter-controls">
              <SlidersHorizontal :size="16" class="filter-icon" /><select
                v-model="filters.category"
                aria-label="按分类筛选"
              >
                <option value="">全部分类</option>
                <option v-for="category in categories" :key="category">
                  {{ category }}
                </option></select
              ><select v-model="filters.status" aria-label="按状态筛选">
                <option value="">全部状态</option>
                <option value="active">在售</option>
                <option value="inactive">已下架</option></select
              ><button v-if="hasFilters" class="text-button" @click="resetFilters">重置</button>
            </div>
          </div>

          <div v-if="error" class="table-state" role="alert">
            <span class="state-icon error-state"><AlertCircle :size="30" /></span>
            <h3>暂时无法加载商品</h3>
            <p>{{ error }}</p>
            <button class="button button-secondary" @click="refresh">
              <RefreshCw :size="15" />重新加载
            </button>
          </div>
          <div v-else class="table-scroll" :aria-busy="loading">
            <table>
              <thead>
                <tr>
                  <th class="product-name-col">商品信息</th>
                  <th>分类</th>
                  <th>售价</th>
                  <th>库存</th>
                  <th>状态</th>
                  <th class="actions-cell">操作</th>
                </tr>
              </thead>
              <tbody v-if="loading">
                <tr v-for="row in 5" :key="row" class="skeleton-row">
                  <td>
                    <div class="skeleton-name">
                      <span class="skeleton skeleton-avatar" /><span
                        class="skeleton skeleton-wide"
                      />
                    </div>
                  </td>
                  <td v-for="col in 5" :key="col">
                    <span class="skeleton skeleton-text" />
                  </td>
                </tr>
              </tbody>
              <tbody v-else-if="products.length">
                <tr v-for="product in products" :key="product.id">
                  <td>
                    <div class="product-identity">
                      <ProductAvatar :product="product" />
                      <div>
                        <button class="product-name" @click="openProduct(product, 'detail')">
                          {{ product.name }}</button><span class="product-sku">{{
                          product.sku
                        }}</span>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="category-label">{{ product.category }}</span>
                  </td>
                  <td class="price-cell">{{ money(product.price) }}</td>
                  <td>
                    <span
                      class="stock-value"
                      :class="{
                        'stock-low': product.status === 'active' && product.stock <= 10,
                      }"
                      ><span
                        v-if="product.status === 'active' && product.stock <= 10"
                        class="mini-dot"
                      />{{ number(product.stock) }}</span
                    >
                  </td>
                  <td>
                    <span
                      class="status-badge"
                      :class="product.status === 'active' ? 'status-active' : 'status-inactive'"
                      ><span class="mini-dot" />{{
                        product.status === 'active' ? '在售' : '已下架'
                      }}</span
                    >
                  </td>
                  <td class="actions-cell">
                    <div class="row-actions">
                      <button
                        class="icon-button"
                        :aria-label="`查看${product.name}`"
                        title="查看详情"
                        @click="openProduct(product, 'detail')"
                      >
                        <Eye :size="17" /></button
                      ><button
                        class="icon-button"
                        :aria-label="`编辑${product.name}`"
                        title="编辑商品"
                        @click="openProduct(product, 'edit')"
                      >
                        <Pencil :size="16" /></button
                      ><button
                        class="icon-button delete-action"
                        :aria-label="`删除${product.name}`"
                        title="删除商品"
                        @click="openProduct(product, 'delete')"
                      >
                        <Trash2 :size="16" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="!loading && !products.length" class="table-state">
              <span class="state-icon"
                ><Search v-if="hasFilters" :size="30" /><Package v-else :size="30"
              /></span>
              <h3>
                {{ hasFilters ? '没有找到匹配的商品' : '从第一件商品开始' }}
              </h3>
              <p>
                {{
                  hasFilters
                    ? '试试其他关键词，或调整一下筛选条件。'
                    : '添加你的商品，在这里开启有序的管理。'
                }}
              </p>
              <button v-if="hasFilters" class="button button-secondary" @click="resetFilters">
                清除筛选</button
              ><button v-else class="button button-primary" @click="openCreate">
                <Plus :size="16" />新增商品
              </button>
            </div>
          </div>

          <footer class="table-footer">
            <span>{{
              loading
                ? '正在加载商品…'
                : total
                  ? `显示 ${Math.min((filters.page - 1) * filters.page_size + 1, total)}–${Math.min(filters.page * filters.page_size, total)} 条，共 ${total} 条`
                  : '共 0 条商品'
            }}</span>
            <div class="pagination">
              <select v-model.number="filters.page_size" aria-label="每页条数">
                <option :value="8">8 条 / 页</option>
                <option :value="16">16 条 / 页</option>
                <option :value="32">32 条 / 页</option></select
              ><button
                class="page-button"
                aria-label="上一页"
                :disabled="filters.page <= 1 || loading"
                @click="filters.page--"
              >
                <ChevronLeft :size="16" /></button
              ><button
                v-for="page in pageNumbers"
                :key="page"
                class="page-button"
                :class="{ 'page-current': filters.page === page }"
                :aria-label="`第 ${page} 页`"
                :aria-current="filters.page === page ? 'page' : undefined"
                :disabled="loading"
                @click="filters.page = page"
              >
                {{ page }}</button
              ><button
                class="page-button"
                aria-label="下一页"
                :disabled="filters.page >= pageCount || loading"
                @click="filters.page++"
              >
                <ChevronRight :size="16" />
              </button>
            </div>
          </footer>
        </section>
        <div class="page-footnote">
          <span><ShieldCheck :size="14" /> 仅登录用户可访问和管理商品</span
          ><a href="http://127.0.0.1:8001/docs" target="_blank" rel="noopener noreferrer"
            ><CircleHelp :size="14" />接口文档<ArrowUpRight :size="13"
          /></a>
        </div>
      </main>
      <footer class="workspace-footer">
        <span>© 2026 Goodstock</span><span>好好管理，好好经营。</span>
      </footer>
    </div>

    <Transition name="toast"
      ><div v-if="toast" class="toast-message" role="status">
        <span><Check :size="15" /></span>{{ toast }}
      </div></Transition
    >

    <BaseModal
      v-if="modal === 'create' || modal === 'edit'"
      :title="modal === 'edit' ? '编辑商品' : '添加新商品'"
      subtitle="完善商品信息，让每一件好物都有迹可循。"
      :busy="saving || modalLoading"
      @close="closeModal"
      ><div v-if="modalLoading" class="modal-loading">
        <span class="spinner dark-spinner" />正在加载商品…
      </div>
      <div v-else-if="modalError && !selected && modal === 'edit'" class="form-error">
        {{ modalError }}
      </div>
      <ProductForm
        v-else
        :key="selected?.id || 'new'"
        :product="selected"
        :busy="saving"
        :error="modalError"
        @submit="saveProduct"
        @cancel="closeModal"
    /></BaseModal>

    <BaseModal
      v-if="modal === 'detail'"
      title="商品详情"
      subtitle="这件商品的完整信息"
      :busy="modalLoading"
      @close="closeModal"
      ><div v-if="modalLoading" class="modal-loading">
        <span class="spinner dark-spinner" />正在加载商品…
      </div>
      <div v-else-if="modalError" class="detail-content">
        <p class="form-error" role="alert">{{ modalError }}</p>
      </div>
      <div v-else class="detail-content">
        <div class="detail-identity">
          <ProductAvatar :product="selected" large />
          <div>
            <h3>{{ selected.name }}</h3>
            <span class="product-sku">{{ selected.sku }}</span>
          </div>
          <span
            class="status-badge"
            :class="selected.status === 'active' ? 'status-active' : 'status-inactive'"
            >{{ selected.status === 'active' ? '在售' : '已下架' }}</span
          >
        </div>
        <dl class="detail-grid">
          <div>
            <dt>商品分类</dt>
            <dd>{{ selected.category }}</dd>
          </div>
          <div>
            <dt>销售价格</dt>
            <dd class="detail-price">{{ money(selected.price) }}</dd>
          </div>
          <div>
            <dt>库存数量</dt>
            <dd>{{ number(selected.stock) }} 件</dd>
          </div>
          <div>
            <dt>商品编号</dt>
            <dd>#{{ selected.id }}</dd>
          </div>
          <div>
            <dt>创建时间</dt>
            <dd>{{ date(selected.created_at) }}</dd>
          </div>
          <div>
            <dt>最近更新</dt>
            <dd>{{ date(selected.updated_at) }}</dd>
          </div>
          <div class="form-full">
            <dt>商品描述</dt>
            <dd class="detail-description">
              {{ selected.description || '暂无描述' }}
            </dd>
          </div>
        </dl>
      </div>
      <footer class="modal-footer">
        <button class="button button-secondary" :disabled="modalLoading" @click="closeModal">
          关闭</button
        ><button
          v-if="!modalError && !modalLoading"
          class="button button-primary"
          @click="modal = 'edit'"
        >
          <Pencil :size="15" />编辑商品
        </button>
      </footer></BaseModal
    >

    <BaseModal
      v-if="modal === 'delete'"
      title="确认删除商品？"
      :busy="saving"
      compact
      @close="closeModal"
      ><div class="delete-content">
        <span class="delete-warning"><Trash2 :size="24" /></span>
        <p>
          即将删除 <strong>「{{ selected.name }}」</strong>。
        </p>
        <p>删除后无法恢复，请确认后继续。</p>
        <p v-if="modalError" class="form-error" role="alert">
          {{ modalError }}
        </p>
      </div>
      <footer class="modal-footer">
        <button class="button button-secondary" :disabled="saving" @click="closeModal">
          保留商品</button
        ><button class="button button-danger" :disabled="saving" @click="deleteProduct">
          <span v-if="saving" class="spinner" /><Trash2 v-else :size="15" />{{
            saving ? '正在删除…' : '确认删除'
          }}
        </button>
      </footer></BaseModal
    >
  </div>
</template>
