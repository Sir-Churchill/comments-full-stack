<template>
  <div class="rte">
    <!-- Toolbar -->
    <div class="rte-toolbar">
      <button
        v-for="tag in tags"
        :key="tag.label"
        type="button"
        class="rte-tag-btn"
        :title="tag.title"
        @click="insertTag(tag)"
      >{{ tag.label }}</button>

      <div class="rte-toolbar-sep"></div>

      <button
        type="button"
        class="rte-preview-btn"
        :class="{ active: showPreview }"
        @click="showPreview = !showPreview"
      >
        {{ showPreview ? 'Edit' : 'Preview' }}
      </button>
    </div>

    <!-- Editor / Preview -->
    <div class="rte-body">
      <Transition name="fade" mode="out-in">
        <div v-if="showPreview" key="preview" class="rte-preview">
          <div class="rte-preview-label">Preview</div>
          <div class="rte-preview-content" v-html="sanitizedPreview"></div>
        </div>
        <textarea
          v-else
          key="editor"
          ref="textareaRef"
          class="rte-textarea"
          :value="modelValue"
          :placeholder="placeholder"
          :rows="rows"
          @input="$emit('update:modelValue', $event.target.value)"
        ></textarea>
      </Transition>
    </div>

    <!-- Validation feedback -->
    <Transition name="slide-up">
      <div v-if="htmlError" class="rte-error">
        <span class="rte-error-icon">⚠</span> {{ htmlError }}
      </div>
    </Transition>

    <div class="rte-hint">
      Allowed tags:
      <code v-for="t in allowedTagNames" :key="t">&lt;{{ t }}&gt;</code>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { validateHtml } from '../utils/validation.js'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Write your comment…' },
  rows: { type: Number, default: 5 },
})
const emit = defineEmits(['update:modelValue', 'validity'])

const textareaRef = ref(null)
const showPreview = ref(false)
const htmlError = ref(null)

const allowedTagNames = ['a', 'code', 'i', 'strong']

const tags = [
  { label: '[i]',      title: 'Italic',    open: '<i>',      close: '</i>' },
  { label: '[strong]', title: 'Bold',      open: '<strong>', close: '</strong>' },
  { label: '[code]',   title: 'Code',      open: '<code>',   close: '</code>' },
  { label: '[a]',      title: 'Link',      open: '<a href="" title="">', close: '</a>' },
]

function insertTag(tag) {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const selected = props.modelValue.slice(start, end)
  const inserted = tag.open + selected + tag.close
  const newVal = props.modelValue.slice(0, start) + inserted + props.modelValue.slice(end)
  emit('update:modelValue', newVal)
  // Restore cursor after Vue re-renders
  setTimeout(() => {
    const pos = selected ? start + inserted.length : start + tag.open.length
    el.setSelectionRange(pos, pos)
    el.focus()
  }, 0)
}

// Validate on every change
watch(() => props.modelValue, (val) => {
  if (!val.trim()) { htmlError.value = null; emit('validity', true); return }
  const result = validateHtml(val)
  htmlError.value = result.error
  emit('validity', result.valid)
})

// Sanitized preview — keep allowed tags only
const sanitizedPreview = computed(() => {
  let html = props.modelValue
  // Strip disallowed tags but keep allowed ones
  html = html.replace(/<(?!\/?(?:a|code|i|strong)\b)[^>]+>/gi, '')
  return html || '<span style="opacity:0.4">Nothing to preview yet…</span>'
})
</script>

<style scoped>
.rte {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: border-color 0.2s;
}
.rte:focus-within {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px rgba(26,20,16,0.08);
}

.rte-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  background: var(--paper-warm);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.rte-tag-btn {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  padding: 4px 9px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--paper);
  color: var(--ink-light);
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.2px;
}
.rte-tag-btn:hover {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
  transform: translateY(-1px);
}
.rte-tag-btn:active { transform: translateY(0); }

.rte-toolbar-sep {
  flex: 1;
}

.rte-preview-btn {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  padding: 4px 12px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition: all 0.15s;
}
.rte-preview-btn:hover,
.rte-preview-btn.active {
  background: var(--teal);
  border-color: var(--teal);
  color: white;
}

.rte-body {
  position: relative;
  min-height: 120px;
}

.rte-textarea {
  display: block;
  width: 100%;
  min-height: 120px;
  padding: 14px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.65;
  color: var(--ink);
  background: var(--paper);
  border: none;
  outline: none;
  resize: vertical;
}

.rte-preview {
  padding: 14px 16px;
  min-height: 120px;
  background: var(--paper);
}

.rte-preview-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 10px;
}

.rte-preview-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--ink);
}
.rte-preview-content :deep(a) { color: var(--accent); }
.rte-preview-content :deep(code) {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--paper-dark);
  padding: 1px 5px;
  border-radius: 2px;
}
.rte-preview-content :deep(strong) { font-weight: 700; }
.rte-preview-content :deep(i) { font-style: italic; }

.rte-error {
  padding: 8px 14px;
  background: #fdf0ef;
  border-top: 1px solid var(--accent-muted);
  font-size: 12px;
  color: var(--accent-dark);
  display: flex;
  align-items: center;
  gap: 6px;
}
.rte-error-icon { font-size: 13px; }

.rte-hint {
  padding: 7px 14px;
  background: var(--paper-warm);
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--ink-faint);
  display: flex;
  align-items: center;
  gap: 5px;
  flex-wrap: wrap;
}
.rte-hint code {
  font-family: var(--font-mono);
  font-size: 10px;
  background: var(--paper-dark);
  padding: 1px 4px;
  border-radius: 2px;
  color: var(--ink-light);
}
</style>