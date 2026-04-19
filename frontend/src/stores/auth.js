import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  async function login(email, password) {
    loading.value = true
    error.value = null
    try {
      const { data } = await authApi.login({ email, password })
      accessToken.value = data.access
      refreshToken.value = data.refresh
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      await fetchMe()
      return true
    } catch (e) {
      error.value = e.response?.data?.detail || 'Invalid credentials'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    error.value = null
    try {
      await authApi.register(payload)
      return await login(payload.email, payload.password)
    } catch (e) {
      const errs = e.response?.data
      if (errs) {
        error.value = Object.values(errs).flat().join(' ')
      } else {
        error.value = 'Registration failed'
      }
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    try {
      const { data } = await authApi.me()
      user.value = data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Restore session on app load
  async function init() {
    if (accessToken.value) await fetchMe()
  }

  return { user, loading, error, isAuthenticated, login, register, logout, init }
})