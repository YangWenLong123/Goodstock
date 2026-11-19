<script setup>
import { computed } from 'vue'
import {
  Archive,
  Backpack,
  Coffee,
  Headphones,
  Keyboard,
  LampDesk,
  Laptop,
  NotebookPen,
  Package,
  PenTool,
  PlugZap,
  ShoppingBag,
} from 'lucide-vue-next'

const props = defineProps({
  product: { type: Object, required: true },
  large: Boolean,
})
const icon = computed(() => {
  const name = props.product.name || ''
  return (
    [
      ['耳机', Headphones],
      ['键盘', Keyboard],
      ['杯', Coffee],
      ['托特', ShoppingBag],
      ['笔记本支架', Laptop],
      ['笔记本', NotebookPen],
      ['台灯', LampDesk],
      ['充电', PlugZap],
      ['签字笔', PenTool],
      ['双肩包', Backpack],
      ['托盘', Archive],
    ].find(([keyword]) => name.includes(keyword))?.[1] || Package
  )
})
</script>

<template>
  <span
    class="product-avatar"
    :class="[
      { large },
      {
        'avatar-digital': product.category === '数码配件',
        'avatar-life': product.category === '生活用品',
        'avatar-stationery': product.category === '办公文具',
        'avatar-bag': product.category === '服饰箱包',
      },
    ]"
    aria-hidden="true"
  >
    <component :is="icon" :size="large ? 36 : 23" :stroke-width="1.5" />
  </span>
</template>
