import { ref, onUnmounted } from 'vue'
import { useCommentsStore } from '../stores/comments.js'

const WS_URL = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/comments/`
const RECONNECT_DELAYS = [1000, 2000, 5000, 10000]

export function useCommentSocket() {
  const store = useCommentsStore()
  const connected = ref(false)
  const authenticated = ref(false)
  const reconnecting = ref(false)

  let socket = null
  let attempt = 0
  let reconnectTimer = null
  let destroyed = false

  function connect() {
    if (destroyed) return

    socket = new WebSocket(WS_URL)

    socket.onopen = () => {
      connected.value = true
      reconnecting.value = false
      attempt = 0

      // Send JWT token as the very first message.
      // Anonymous users don't send auth — they still receive broadcasts.
      const token = localStorage.getItem('access_token')
      if (token) {
        socket.send(JSON.stringify({ type: 'auth', token }))
      }
    }

    socket.onmessage = (event) => {
      let msg
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }

      switch (msg.type) {
        case 'auth.result':
          authenticated.value = msg.authenticated
          break

        case 'comment.new':
          handleNewComment(msg.comment)
          break

        case 'comment.deleted':
          handleDeleted(msg.id)
          break

        case 'error':
          console.warn('[WS]', msg.message)
          break
      }
    }

    socket.onclose = (event) => {
      connected.value = false
      authenticated.value = false

      // 4001 = token expired (server can send this code on demand)
      if (event.code === 4001) {
        tryRefreshThenReconnect()
        return
      }

      if (!destroyed) scheduleReconnect()
    }

    socket.onerror = () => {
      // onclose fires right after — reconnect is handled there
    }
  }

  // If the server closes with 4001 (token expired), silently refresh
  // the access token and reconnect with the new one.
  async function tryRefreshThenReconnect() {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) { scheduleReconnect(); return }

    try {
      const res = await fetch('/api/users/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      })
      if (!res.ok) throw new Error('refresh failed')
      const data = await res.json()
      localStorage.setItem('access_token', data.access)
    } catch {
      // Refresh failed — just reconnect anonymously
    }

    if (!destroyed) connect()
  }

  function scheduleReconnect() {
    reconnecting.value = true
    const delay = RECONNECT_DELAYS[Math.min(attempt, RECONNECT_DELAYS.length - 1)]
    attempt++
    reconnectTimer = setTimeout(connect, delay)
  }

  // ── Comment tree helpers ──────────────────────────────────────────────────

  function handleNewComment(comment) {
    if (!comment.parent) {
      const exists = store.comments.some(c => c.id === comment.id)
      if (!exists) {
        store.comments.unshift(comment)
        store.pagination.count++
      }
      return
    }
    insertReply(store.comments, comment)
  }

  function insertReply(comments, reply) {
    for (const c of comments) {
      if (c.id === reply.parent) {
        if (!c.children) c.children = []
        const exists = c.children.some(ch => ch.id === reply.id)
        if (!exists) c.children.push(reply)
        return true
      }
      if (c.children?.length && insertReply(c.children, reply)) return true
    }
    return false
  }

  function handleDeleted(id) {
    const idx = store.comments.findIndex(c => c.id === id)
    if (idx !== -1) {
      store.comments.splice(idx, 1)
      store.pagination.count--
      return
    }
    removeFromChildren(store.comments, id)
  }

  function removeFromChildren(comments, id) {
    for (const c of comments) {
      if (c.children?.length) {
        const idx = c.children.findIndex(ch => ch.id === id)
        if (idx !== -1) { c.children.splice(idx, 1); return }
        removeFromChildren(c.children, id)
      }
    }
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  function disconnect() {
    destroyed = true
    clearTimeout(reconnectTimer)
    socket?.close()
  }

  onUnmounted(disconnect)
  connect()

  return { connected, authenticated, reconnecting, disconnect }
}