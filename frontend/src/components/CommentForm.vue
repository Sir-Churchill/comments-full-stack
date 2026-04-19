<template>
  <div class="comment-form" :class="{ 'comment-form--reply': isReply }">
    <div class="form-header">
      <h3 class="form-title">
        <template v-if="isReply">↩ Reply to comment</template>
        <template v-else>Leave a comment</template>
      </h3>
      <button v-if="isReply" type="button" class="form-cancel" @click="$emit('cancel')">Cancel</button>
    </div>

    <!-- Prefilled user info strip -->
    <div class="form-user-strip" v-if="auth.user">
      <div class="fus-avatar" :style="{ background: avatarColor }">{{ initials }}</div>
      <div class="fus-info">
        <span class="fus-name">{{ auth.user.username }}</span>
        <span class="fus-email">{{ auth.user.email }}</span>
        <a v-if="auth.user.home_page" :href="auth.user.home_page" class="fus-url" target="_blank" rel="noopener">
          ↗ {{ cleanUrl(auth.user.home_page) }}
        </a>
      </div>
      <span class="fus-badge">posting as you</span>
    </div>

    <form @submit.prevent="submit" novalidate>
      <!-- Text editor -->
      <div class="field">
        <label class="field-label">Message</label>
        <RichTextEditor
          v-model="form.text"
          :placeholder="isReply ? 'Write your reply…' : 'Share your thoughts…'"
          @validity="htmlValid = $event"
        />
        <div v-if="errors.text" class="field-error">{{ errors.text }}</div>
      </div>

      <!-- Attachments -->
      <div class="field">
        <label class="field-label">Attachment <span class="field-optional">(optional)</span></label>
        <FileUpload
          @update:image="form.image = $event"
          @update:file="form.file = $event"
        />
      </div>

      <!-- Captcha -->
      <div class="field field--captcha">
        <label class="field-label">Security check</label>
        <div class="captcha-wrap">
          <div class="captcha-image-wrap">
            <img
              v-if="captcha.image_url"
              :src="captcha.image_url"
              class="captcha-image"
              alt="captcha"
            />
            <div v-else class="captcha-placeholder">
              <span class="spinner"></span>
            </div>
            <button type="button" class="captcha-refresh" title="Get new captcha" @click="loadCaptcha">↻</button>
          </div>
          <input
            v-model="form.captcha_value"
            class="captcha-input"
            placeholder="Enter the text above"
            autocomplete="off"
          />
        </div>
        <div v-if="errors.captcha" class="field-error">{{ errors.captcha }}</div>
      </div>

      <Transition name="slide-up">
        <div v-if="submitError" class="form-error">{{ submitError }}</div>
      </Transition>

      <div class="form-actions">
        <button type="submit" class="btn-submit" :disabled="submitting || !htmlValid">
          <span v-if="submitting" class="spinner spinner--white"></span>
          <span v-else>{{ isReply ? 'Post reply' : 'Post comment' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useCommentsStore } from '../stores/comments.js'
import { useAuthStore } from '../stores/auth.js'
import RichTextEditor from './RichTextEditor.vue'
import FileUpload from './FileUpload.vue'

const props = defineProps({
  parentId: { type: Number, default: null },
  isReply: { type: Boolean, default: false },
})
const emit = defineEmits(['submitted', 'cancel'])

const store = useCommentsStore()
const auth = useAuthStore()

const initials = computed(() => (auth.user?.username || '?').slice(0, 2).toUpperCase())
const avatarColor = computed(() => {
  let hash = 0
  for (const c of (auth.user?.username || '')) hash = c.charCodeAt(0) + ((hash << 5) - hash)
  const colors = ['#c8433a','#2a7a6e','#b8860b','#5a6e8a','#7a5a6e','#4a7a5a']
  return colors[Math.abs(hash) % colors.length]
})
function cleanUrl(url) {
  return url?.replace(/^https?:\/\//, '').replace(/\/$/, '') || ''
}

const form = reactive({ text: '', captcha_key: '', captcha_value: '', image: null, file: null })
const errors = reactive({})
const submitError = ref(null)
const submitting = ref(false)
const htmlValid = ref(true)
const captcha = reactive({ image_url: '', key: '' })

onMounted(loadCaptcha)

async function loadCaptcha() {
  captcha.image_url = ''
  const data = await store.getCaptcha()
  captcha.image_url = data.image_url
  captcha.key = data.key
  form.captcha_key = data.key
  form.captcha_value = ''
}

function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  let ok = true
  if (!form.text.trim()) { errors.text = 'Message is required.'; ok = false }
  if (!htmlValid.value) { errors.text = 'Fix HTML tag errors before submitting.'; ok = false }
  if (!form.captcha_value.trim()) { errors.captcha = 'Please solve the captcha.'; ok = false }
  return ok
}

async function submit() {
  if (!validate()) return
  submitting.value = true
  submitError.value = null

  try {
    const fd = new FormData()
    fd.append('text', form.text)
    fd.append('captcha_key', form.captcha_key)
    fd.append('captcha_value', form.captcha_value)
    if (props.parentId) fd.append('parent', props.parentId)
    if (form.image) fd.append('image', form.image)
    if (form.file) fd.append('file', form.file)

    const comment = await store.createComment(fd)
    form.text = ''
    form.captcha_value = ''
    form.image = null
    form.file = null
    emit('submitted', comment)
    await loadCaptcha()
  } catch (e) {
    const data = e.response?.data
    if (data) {
      if (data.captcha) { errors.captcha = Array.isArray(data.captcha) ? data.captcha.join(' ') : data.captcha }
      if (data.text) { errors.text = Array.isArray(data.text) ? data.text.join(' ') : data.text }
      if (data.non_field_errors) submitError.value = data.non_field_errors.join(' ')
      else if (!data.captcha && !data.text) submitError.value = 'Submission failed. Please try again.'
    } else {
      submitError.value = 'Network error. Please try again.'
    }
    // Refresh captcha on failure
    await loadCaptcha()
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.comment-form {
  background: var(--paper);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 28px;
  box-shadow: var(--shadow-sm);
}

.comment-form--reply {
  padding: 20px;
  border-left: 3px solid var(--gold);
  background: var(--paper-warm);
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.form-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
}

.form-cancel {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--ink-faint);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius);
  transition: all 0.15s;
}
.form-cancel:hover { background: var(--paper-dark); color: var(--accent); }

.field { margin-bottom: 20px; }

.field-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 8px;
}

.field-optional {
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  font-size: 11px;
}

.field-error {
  margin-top: 6px;
  font-size: 12px;
  color: var(--accent-dark);
}

/* Captcha */
.captcha-wrap {
  display: flex;
  gap: 12px;
  align-items: stretch;
  flex-wrap: wrap;
}

.captcha-image-wrap {
  position: relative;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 120px;
  background: var(--paper-warm);
}

.captcha-image {
  display: block;
  height: 40px;
  width: auto;
}

.captcha-placeholder {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
}

.captcha-refresh {
  position: absolute;
  bottom: 2px; right: 3px;
  background: rgba(245,240,232,0.85);
  border: none;
  width: 18px; height: 18px;
  border-radius: 50%;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink-light);
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
  line-height: 1;
}
.captcha-refresh:hover { background: var(--ink); color: white; transform: rotate(90deg); }

.captcha-input {
  flex: 1;
  min-width: 140px;
  padding: 10px 14px;
  font-family: var(--font-mono);
  font-size: 14px;
  letter-spacing: 2px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--paper);
  color: var(--ink);
  outline: none;
  transition: border-color 0.2s;
}
.captcha-input:focus { border-color: var(--ink); box-shadow: 0 0 0 3px rgba(26,20,16,0.08); }

/* Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.btn-submit {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  padding: 10px 28px;
  background: var(--ink);
  color: var(--paper);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.18s;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
  justify-content: center;
}
.btn-submit:hover:not(:disabled) { background: var(--accent); transform: translateY(-1px); box-shadow: var(--shadow-md); }
.btn-submit:active:not(:disabled) { transform: translateY(0); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.form-error {
  padding: 10px 14px;
  background: #fdf0ef;
  border: 1px solid var(--accent-muted);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--accent-dark);
  margin-bottom: 16px;
}

/* User strip */
.form-user-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--paper-dark);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 20px;
}
.fus-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  color: white;
  font-family: var(--font-display);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.fus-info {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
}
.fus-name { font-size: 13px; font-weight: 700; color: var(--ink); }
.fus-email { font-size: 11px; color: var(--ink-faint); }
.fus-url { font-size: 11px; color: var(--teal); text-decoration: none; }
.fus-url:hover { text-decoration: underline; }
.fus-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--teal);
  background: rgba(42,122,110,0.1);
  padding: 2px 7px;
  border-radius: 10px;
  white-space: nowrap;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(26,20,16,0.2);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
.spinner--white {
  border-color: rgba(255,255,255,0.3);
  border-top-color: white;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>