<template>
  <header class="nav">
    <div class="nav-inner">
      <RouterLink to="/" class="nav-brand">
        <span class="brand-mark">D</span>
        <span class="brand-name">Discourse</span>
      </RouterLink>

      <nav class="nav-links">
        <template v-if="auth.isAuthenticated">
          <!-- User chip with dropdown -->
          <div class="user-chip" ref="chipRef" @click="menuOpen = !menuOpen">
            <div class="user-chip-avatar" :style="{ background: avatarColor }">
              {{ initials }}
            </div>
            <span class="user-chip-name">{{ auth.user?.username }}</span>
            <span class="user-chip-arrow" :class="{ open: menuOpen }">▾</span>
          </div>

          <Transition name="dropdown">
            <div v-if="menuOpen" class="user-menu">
              <div class="user-menu-header">
                <div class="umh-avatar" :style="{ background: avatarColor }">{{ initials }}</div>
                <div>
                  <div class="umh-name">{{ auth.user?.username }}</div>
                  <div class="umh-email">{{ auth.user?.email }}</div>
                </div>
              </div>
              <div class="user-menu-sep"></div>
              <button class="user-menu-item user-menu-item--danger" @click="handleLogout">
                <span>↪</span> Sign out
              </button>
            </div>
          </Transition>
        </template>

        <template v-else>
          <RouterLink to="/login" class="nav-btn nav-btn--ghost">Sign in</RouterLink>
          <RouterLink to="/register" class="nav-btn nav-btn--primary">Join</RouterLink>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const menuOpen = ref(false)
const chipRef = ref(null)

const initials = computed(() => (auth.user?.username || '?').slice(0, 2).toUpperCase())

const avatarColor = computed(() => {
  let hash = 0
  for (const c of (auth.user?.username || '')) hash = c.charCodeAt(0) + ((hash << 5) - hash)
  const colors = ['#c8433a','#2a7a6e','#b8860b','#5a6e8a','#7a5a6e','#4a7a5a']
  return colors[Math.abs(hash) % colors.length]
})

function handleLogout() {
  menuOpen.value = false
  auth.logout()
  router.push('/login')
}

function onClickOutside(e) {
  if (chipRef.value && !chipRef.value.contains(e.target)) menuOpen.value = false
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.nav {
  position: sticky;
  top: 0;
  z-index: 200;
  background: rgba(245, 240, 232, 0.94);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
}

.nav-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.brand-mark {
  width: 32px; height: 32px;
  background: var(--ink);
  color: var(--paper);
  font-family: var(--font-display);
  font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  border-radius: 2px;
  letter-spacing: -0.5px;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 20px; font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.3px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

/* User chip */
.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 6px;
  border: 1px solid var(--border-strong);
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.18s;
  user-select: none;
  background: var(--paper);
}
.user-chip:hover { border-color: var(--ink); background: var(--paper-warm); }

.user-chip-avatar {
  width: 26px; height: 26px;
  border-radius: 50%;
  color: white;
  font-family: var(--font-display);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.user-chip-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.2px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-chip-arrow {
  font-size: 10px;
  color: var(--ink-faint);
  transition: transform 0.2s;
  display: inline-block;
}
.user-chip-arrow.open { transform: rotate(180deg); }

/* Dropdown menu */
.user-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  min-width: 220px;
  background: var(--paper);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  z-index: 300;
}

.user-menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--paper-warm);
}

.umh-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  color: white;
  font-family: var(--font-display);
  font-size: 14px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.umh-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
}

.umh-email {
  font-size: 11px;
  color: var(--ink-faint);
  margin-top: 1px;
}

.user-menu-sep {
  height: 1px;
  background: var(--border);
}

.user-menu-item {
  width: 100%;
  padding: 11px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-light);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}
.user-menu-item:hover { background: var(--paper-warm); color: var(--ink); }
.user-menu-item--danger:hover { background: #fdf0ef; color: var(--accent); }

/* Auth buttons */
.nav-btn {
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  padding: 7px 16px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.18s ease;
  text-decoration: none;
  border: 1px solid transparent;
}
.nav-btn--ghost {
  color: var(--ink-light);
  background: transparent;
  border-color: var(--border-strong);
}
.nav-btn--ghost:hover { background: var(--paper-dark); color: var(--ink); }
.nav-btn--primary { color: var(--paper); background: var(--ink); border-color: var(--ink); }
.nav-btn--primary:hover { background: var(--accent); border-color: var(--accent); }

/* Dropdown animation */
.dropdown-enter-active { transition: all 0.2s cubic-bezier(0.34, 1.4, 0.64, 1); }
.dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from { opacity: 0; transform: translateY(-8px) scale(0.96); }
.dropdown-leave-to { opacity: 0; transform: translateY(-4px) scale(0.98); }
</style>