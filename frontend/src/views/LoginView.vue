<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Decorative column -->
      <div class="auth-deco">
        <div class="deco-quote">
          <span class="deco-mark">"</span>
          <p>Great conversations start with a single voice.</p>
        </div>
        <div class="deco-brand">
          <span class="deco-d">D</span>
          <span class="deco-name">Discourse</span>
        </div>
      </div>

      <!-- Form column -->
      <div class="auth-main">
        <div class="auth-header">
          <h1 class="auth-title">Welcome back</h1>
          <p class="auth-sub">Sign in to join the conversation</p>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit" novalidate>
          <div class="field">
            <label class="field-label" for="email">Email</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="field-input"
              :class="{ error: errors.email }"
              placeholder="you@example.com"
              autocomplete="email"
            />
            <div v-if="errors.email" class="field-error">{{ errors.email }}</div>
          </div>

          <div class="field">
            <label class="field-label" for="password">Password</label>
            <div class="input-wrap">
              <input
                id="password"
                v-model="form.password"
                :type="showPw ? 'text' : 'password'"
                class="field-input"
                :class="{ error: errors.password }"
                placeholder="••••••••"
                autocomplete="current-password"
              />
              <button type="button" class="pw-toggle" @click="showPw = !showPw">
                {{ showPw ? '🙈' : '👁' }}
              </button>
            </div>
            <div v-if="errors.password" class="field-error">{{ errors.password }}</div>
          </div>

          <Transition name="slide-up">
            <div v-if="auth.error" class="form-error">
              <span class="form-error-icon">⚠</span> {{ auth.error }}
            </div>
          </Transition>

          <button type="submit" class="btn-submit" :disabled="auth.loading">
            <span v-if="auth.loading" class="spinner"></span>
            <span v-else>Sign in</span>
          </button>
        </form>

        <div class="auth-footer">
          <span>Don't have an account?</span>
          <RouterLink to="/register" class="auth-link">Create one →</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const form = reactive({ email: '', password: '' })
const errors = reactive({})
const showPw = ref(false)

function validate() {
  Object.keys(errors).forEach(k => delete errors[k])
  let ok = true
  if (!form.email) { errors.email = 'Email is required.'; ok = false }
  else if (!/\S+@\S+\.\S+/.test(form.email)) { errors.email = 'Enter a valid email.'; ok = false }
  if (!form.password) { errors.password = 'Password is required.'; ok = false }
  return ok
}

async function handleSubmit() {
  if (!validate()) return
  const ok = await auth.login(form.email, form.password)
  if (ok) router.push('/')
}
</script>

<style scoped>
.auth-page {
  min-height: calc(100vh - 60px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.auth-card {
  display: flex;
  width: 100%;
  max-width: 760px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  animation: cardIn 0.4s cubic-bezier(0.34, 1.2, 0.64, 1) both;
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(24px) scale(0.97); }
  to { opacity: 1; transform: none; }
}

/* Decorative panel */
.auth-deco {
  width: 240px;
  flex-shrink: 0;
  background: var(--ink);
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
}
.auth-deco::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 80% 20%, rgba(200,67,58,0.25) 0%, transparent 60%),
              radial-gradient(ellipse at 20% 80%, rgba(184,134,11,0.2) 0%, transparent 60%);
  pointer-events: none;
}

.deco-quote {
  position: relative;
  z-index: 1;
}
.deco-mark {
  font-family: var(--font-display);
  font-size: 72px;
  line-height: 0.7;
  color: rgba(255,255,255,0.12);
  display: block;
  margin-bottom: 12px;
}
.deco-quote p {
  font-family: var(--font-display);
  font-size: 15px;
  font-style: italic;
  color: rgba(255,255,255,0.65);
  line-height: 1.6;
}

.deco-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}
.deco-d {
  width: 30px; height: 30px;
  border: 1.5px solid rgba(255,255,255,0.3);
  border-radius: 2px;
  color: rgba(255,255,255,0.7);
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.deco-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: rgba(255,255,255,0.5);
  letter-spacing: -0.3px;
}

/* Main panel */
.auth-main {
  flex: 1;
  background: var(--paper);
  padding: 48px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.auth-header { margin-bottom: 32px; }

.auth-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.5px;
  margin-bottom: 6px;
}

.auth-sub {
  font-size: 14px;
  color: var(--ink-faint);
}

.auth-form { display: flex; flex-direction: column; gap: 20px; }

.field { display: flex; flex-direction: column; gap: 7px; }

.field-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.input-wrap { position: relative; }

.field-input {
  width: 100%;
  padding: 11px 14px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--ink);
  background: var(--paper-warm);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  outline: none;
  transition: all 0.18s;
}
.field-input:focus {
  border-color: var(--ink);
  background: var(--paper);
  box-shadow: 0 0 0 3px rgba(26,20,16,0.08);
}
.field-input.error { border-color: var(--accent); background: #fdf8f8; }

.input-wrap .field-input { padding-right: 42px; }
.pw-toggle {
  position: absolute;
  right: 10px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  cursor: pointer; font-size: 14px;
  opacity: 0.5; transition: opacity 0.15s;
}
.pw-toggle:hover { opacity: 1; }

.field-error { font-size: 12px; color: var(--accent-dark); }

.form-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #fdf0ef;
  border: 1px solid var(--accent-muted);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--accent-dark);
}
.form-error-icon { font-size: 14px; }

.btn-submit {
  width: 100%;
  padding: 12px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  background: var(--ink);
  color: var(--paper);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.18s;
  display: flex; align-items: center; justify-content: center;
  gap: 8px;
  margin-top: 4px;
}
.btn-submit:hover:not(:disabled) {
  background: var(--accent);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.auth-footer {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-faint);
}
.auth-link {
  font-weight: 700;
  color: var(--accent);
  text-decoration: none;
  transition: color 0.15s;
}
.auth-link:hover { color: var(--accent-dark); }

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .auth-deco { display: none; }
  .auth-main { padding: 32px 24px; }
}
</style>