<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { X } from 'lucide-vue-next'

const props = defineProps({
  title: String,
  subtitle: String,
  busy: Boolean,
  compact: Boolean,
})
const emit = defineEmits(['close'])
const panel = ref(null)
const previousFocus = document.activeElement
const previousOverflow = document.body.style.overflow

function close() {
  if (!props.busy) emit('close')
}

function keydown(event) {
  if (event.key === 'Escape') close()
  if (event.key !== 'Tab') return
  const focusable = [
    ...panel.value.querySelectorAll('button, input, textarea, select, [tabindex="0"]'),
  ].filter((element) => !element.disabled && element.offsetParent !== null)
  const first = focusable[0]
  const last = focusable.at(-1)
  if (!first) {
    event.preventDefault()
    panel.value.focus()
  } else if (document.activeElement === panel.value) {
    event.preventDefault()
    ;(event.shiftKey ? last : first).focus()
  } else if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(async () => {
  document.body.style.overflow = 'hidden'
  document.addEventListener('keydown', keydown)
  await nextTick()
  const focusTarget = panel.value.querySelector('[autofocus]') || panel.value
  focusTarget.focus()
})

onUnmounted(() => {
  document.body.style.overflow = previousOverflow
  document.removeEventListener('keydown', keydown)
  previousFocus?.focus()
})
</script>

<template>
  <Teleport to="body">
    <div class="modal-backdrop" @mousedown.self="close">
      <section
        ref="panel"
        class="modal"
        :class="{ 'modal-compact': compact }"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabindex="-1"
        :aria-busy="busy"
      >
        <header class="modal-header">
          <div>
            <h2 id="modal-title">{{ title }}</h2>
            <p v-if="subtitle">{{ subtitle }}</p>
          </div>
          <button
            class="icon-button"
            type="button"
            aria-label="关闭弹窗"
            :disabled="busy"
            @click="close"
          >
            <X :size="20" />
          </button>
        </header>
        <slot />
      </section>
    </div>
  </Teleport>
</template>
