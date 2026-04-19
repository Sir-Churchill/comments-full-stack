<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- Decorative panel -->
      <div class="auth-deco">
        <div class="deco-steps">
          <div
            v-for="(step, i) in steps"
            :key="i"
            class="deco-step"
            :class="{ active: currentStep === i, done: currentStep > i }"
          >
            <span class="step-num">{{ currentStep > i ? '✓' : i + 1 }}</span>
            <span class="step-label">{{ step }}</span>
          </div>
        </div>
        <div class="deco-brand">
          <span class="deco-d">D</span>
          <span class="deco-name">Discourse</span>
        </div>
      </div>

      <!-- Form -->
      <div class="auth-main">
        <div class="auth-header">
          <h1 class="auth-title">Create account</h1>
          <p class="auth-sub">Join the conversation in seconds</p>
        </div>

        <form class="auth-form" @submit.prevent="handleSubmit" novalidate>
          <!-- Step 0: credentials -->
          <Transition name="step" mode="out-in">
            <div v-if="currentStep === 0" key="s0" class="step-fields">
              <div class="field">
                <label class="field-label" for="reg-email">Email</label>
                <input
                  id="reg-email"
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
                <label class="field-label" for="reg-password">Password</label>
                <div class="input-wrap">
                  <input
                    id="reg-password"
                    v-model="form.password"
                    :type="showPw ? 'text' : 'password'"
                    class="field-input"
                    :class="{ error: errors.password }"
                    placeholder="Min 8 characters"
                    autocomplete="new-password"
                  />
                  <button type="button" class="pw-toggle" @click="showPw = !showPw">
                    {{ showPw ? '🙈' : '👁' }}
                  </button>
                </div>
                <div v-if="errors.password" class="field-error">{{ errors.password }}</div>
                <div class="pw-strength" v-if="form.password">
                  <div
                    v-for="n in 4" :key="n"
                    class="pw-bar"
                    :class="{ filled: passwordStrength >= n, [`strength-${passwordStrength}`]: true }"
                  ></div>
                  <span class="pw-label">{{ pwLabels[passwordStrength - 1] || '' }}</span>
                </div>
              </div>
              <button type="button" class="btn-next" @click="nextStep">
                Continue →
              </button>
            </div>

            <!-- Step 1: profile -->
            <div v-else-if="currentStep === 1" key="s1" class="step-fields">
              <div class="field">
                <label class="field-label" for="reg-username">Username</label>
                <input
                  id="reg-username"
                  v-model="form.username"
                  type="text"
                  class="field-input"
                  :class="{ error: errors.username }"
                  placeholder="Letters and numbers only"
                  autocomplete="username"
                />
                <div v-if="errors.username" class="field-error">{{ errors.username }}</div>
              </div>
              <div class="field">
                <label class="field-label" for="reg-homepage">
                  Home page <span class="field-optional">(optional)</span>
                </label>
                <input
                  id="reg-homepage"
                  v-model="form.home_page"
                  type="url"
                  class="field-input"
                  :class="{ error: errors.home_page }"
                  placeholder="https://yoursite.com"
                />
                <div v-if="errors.home_page" class="field-error">{{ errors.home_page }}</div>
              </div>

              <Transition name="slide-up">
                <div v-if="auth.error" class="form-error">
                  <span>⚠</span> {{ auth.error }}
                </div>
              </Transition>

              <div class="step-nav">
                <button type="button" class="btn-back" @click="currentStep = 0">← Back</button>
                <button type="submit" class="btn-submit" :disabled="auth.loading">
                  <span v-if="auth.loading" class="spinner"></span>
                  <span v-else>Create account</span>
                </button>
              </div>
            </div>
          </Transition>
        </form>

        <div class="auth-footer">
          <span>Already have an account?</span>
          <RouterLink to="/login" class="auth-link">Sign in →</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const steps = ['Credentials', 'Profile']
const currentStep = ref(0)
const showPw = ref(false)
const pwLabels = ['Weak', 'Fair', 'Good', 'Strong']

const form = reactive({ email: '', password: '', username: '', home_page: '' })
const errors = reactive({})

const passwordStrength = computed(() => {
  const p = form.password
  if (!p) return 0
  let s = 0
  if (p.length >= 8) s++
  if (/[A-Z]/.test(p)) s++
  if (/[0-9]/.test(p)) s++
  if (/[^A-Za-z0-9]/.test(p)) s++
  return Math.max(s, 1)
})

function validateStep0() {
  Object.keys(errors).forEach(k => delete errors[k])
  let ok = true
  if (!form.email) { errors.email = 'Email is required.'; ok = false }
  else if (!/\S+@\S+\.\S+/.test(form.email)) { errors.email = 'Enter a valid email.'; ok = false }
  if (!form.password) { errors.password = 'Password is required.'; ok = false }
  else if (form.password.length < 8) { errors.password = 'At least 8 characters required.'; ok = false }
  return ok
}

function validateStep1() {
  Object.keys(errors).forEach(k => delete errors[k])
  let ok = true
  if (!form.username) { errors.username = 'Username is required.'; ok = false }
  else if (!/^[a-zA-Z0-9]+$/.test(form.username)) { errors.username = 'Letters and numbers only.'; ok = false }
  if (form.home_page && !/^https?:\/\/.+/.test(form.home_page)) {
    errors.home_page = 'Must start with http:// or https://'
    ok = false
  }
  return ok
}

function nextStep() {
  if (validateStep0()) currentStep.value = 1
}

async function handleSubmit() {
  if (!validateStep1()) return

  const payload = {
    email: form.email,
    password: form.password,
    username: form.username
  }
  if (form.home_page) payload.home_page = form.home_page

  auth.error = null

  const registered = await auth.register(payload)
  if (registered) await router.push('/')
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

/* Deco panel */
.auth-deco {
  width: 220px;
  flex-shrink: 0;
  background: var(--ink);
  padding: 40px 28px;
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
  background: radial-gradient(ellipse at 20% 30%, rgba(42,122,110,0.3) 0%, transparent 60%),
              radial-gradient(ellipse at 80% 80%, rgba(184,134,11,0.2) 0%, transparent 60%);
  pointer-events: none;
}

.deco-steps {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: relative;
  z-index: 1;
}

.deco-step {
  display: flex;
  align-items: center;
  gap: 12px;
  opacity: 0.35;
  transition: all 0.3s;
}
.deco-step.active { opacity: 1; }
.deco-step.done { opacity: 0.6; }

.step-num {
  width: 26px; height: 26px;
  border: 1.5px solid rgba(255,255,255,0.4);
  border-radius: 50%;
  color: rgba(255,255,255,0.8);
  font-size: 11px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: all 0.3s;
}
.deco-step.active .step-num {
  background: white;
  color: var(--ink);
  border-color: white;
}
.deco-step.done .step-num {
  background: var(--teal);
  border-color: var(--teal);
  color: white;
}

.step-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255,255,255,0.7);
  letter-spacing: 0.3px;
}
.deco-step.active .step-label { color: white; }

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
}

/* Main */
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
.auth-sub { font-size: 14px; color: var(--ink-faint); }

.auth-form { position: relative; }

.step-fields { display: flex; flex-direction: column; gap: 20px; }

.field { display: flex; flex-direction: column; gap: 7px; }

.field-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.field-optional { font-weight: 400; text-transform: none; letter-spacing: 0; font-size: 11px; }

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
.field-input.error { border-color: var(--accent); }

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

.pw-strength {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}
.pw-bar {
  flex: 1;
  height: 3px;
  border-radius: 2px;
  background: var(--border-strong);
  transition: background 0.3s;
}
.pw-bar.filled.strength-1 { background: var(--accent); }
.pw-bar.filled.strength-2 { background: var(--gold); }
.pw-bar.filled.strength-3 { background: var(--teal-light); }
.pw-bar.filled.strength-4 { background: var(--teal); }
.pw-label { font-size: 10px; color: var(--ink-faint); white-space: nowrap; margin-left: 4px; }

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

.step-nav {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-back {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 11px 16px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition: all 0.15s;
}
.btn-back:hover { background: var(--paper-dark); color: var(--ink); }

.btn-next, .btn-submit {
  flex: 1;
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
}
.btn-next:hover, .btn-submit:hover:not(:disabled) {
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

/* Step transition */
.step-enter-active { transition: all 0.25s ease; }
.step-leave-active { transition: all 0.18s ease; }
.step-enter-from { opacity: 0; transform: translateX(20px); }
.step-leave-to { opacity: 0; transform: translateX(-20px); }

@media (max-width: 600px) {
  .auth-deco { display: none; }
  .auth-main { padding: 32px 24px; }
}
</style>