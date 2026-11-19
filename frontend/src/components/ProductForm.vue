<script setup>
import { reactive, ref } from 'vue'
import { Check, Info } from 'lucide-vue-next'

const props = defineProps({ product: Object, busy: Boolean, error: String })
const emit = defineEmits(['submit', 'cancel'])
const categories = ['数码配件', '办公文具', '生活用品', '服饰箱包']
const form = reactive({
  name: props.product?.name || '',
  sku: props.product?.sku || '',
  category: props.product?.category || '数码配件',
  price: props.product?.price || '',
  stock: props.product?.stock ?? 0,
  status: props.product?.status || 'active',
  description: props.product?.description || '',
})
const localError = ref('')

function submit() {
  if (props.busy) return
  localError.value = ''
  if (!form.name.trim()) {
    localError.value = '请输入商品名称，不能只有空格。'
    return
  }
  if (!Number.isInteger(form.stock)) {
    localError.value = '库存必须是整数。'
    return
  }
  emit('submit', {
    ...form,
    name: form.name.trim(),
    sku: form.sku.trim().toUpperCase(),
  })
}
</script>

<template>
  <form @submit.prevent="submit">
    <fieldset class="product-form" :disabled="busy">
      <div class="form-full">
        <label class="field-label" for="product-name"
          >商品名称 <span class="required">*</span></label
        ><input
          id="product-name"
          v-model="form.name"
          placeholder="例如：无线降噪耳机"
          required
          maxlength="100"
          autofocus
        />
      </div>
      <div>
        <label class="field-label" for="product-sku"
          >商品编码 SKU <span class="required">*</span></label
        ><input
          id="product-sku"
          v-model="form.sku"
          placeholder="例如：DG-001"
          required
          maxlength="50"
          pattern="[a-zA-Z0-9_\-]+"
          title="仅支持英文字母、数字、下划线和短横线"
        />
        <p class="field-help">唯一编码，支持字母、数字、- 和 _</p>
      </div>
      <div>
        <label class="field-label" for="product-category"
          >商品分类 <span class="required">*</span></label
        ><select id="product-category" v-model="form.category">
          <option v-for="category in categories" :key="category">
            {{ category }}
          </option>
        </select>
      </div>
      <div>
        <label class="field-label" for="product-price"
          >销售价格 <span class="required">*</span></label
        >
        <div class="price-input">
          <span>¥</span
          ><input
            id="product-price"
            v-model="form.price"
            type="number"
            min="0.01"
            max="99999999.99"
            step="0.01"
            placeholder="0.00"
            required
          />
        </div>
      </div>
      <div>
        <label class="field-label" for="product-stock"
          >库存数量 <span class="required">*</span></label
        ><input
          id="product-stock"
          v-model.number="form.stock"
          type="number"
          min="0"
          max="1000000"
          step="1"
          required
        />
      </div>
      <div class="form-full">
        <label class="field-label" for="product-status">商品状态</label
        ><select id="product-status" v-model="form.status">
          <option value="active">在售 · 可正常销售</option>
          <option value="inactive">已下架 · 暂停销售</option>
        </select>
      </div>
      <div class="form-full">
        <label class="field-label" for="product-description"
          >商品描述 <span class="optional">选填</span></label
        ><textarea
          id="product-description"
          v-model="form.description"
          rows="3"
          maxlength="2000"
          placeholder="介绍一下这件商品的特点…"
        /><span class="character-count">{{ form.description.length }} / 2000</span>
      </div>
      <p class="form-tip form-full">
        <Info :size="15" /> 在售商品库存不超过 10 件时，将显示库存预警。
      </p>
      <p v-if="localError || error" class="form-error form-full" role="alert">
        {{ localError || error }}
      </p>
    </fieldset>
    <footer class="modal-footer">
      <button
        type="button"
        class="button button-secondary"
        :disabled="busy"
        @click="emit('cancel')"
      >
        取消</button
      ><button class="button button-primary" type="submit" :disabled="busy">
        <span v-if="busy" class="spinner" /><Check v-else :size="16" />{{
          busy ? '正在保存…' : '保存商品'
        }}
      </button>
    </footer>
  </form>
</template>
