<template>
  <div class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-label">Open discussion</div>
        <h1 class="hero-title">Discourse</h1>
        <p class="hero-sub">A space for thoughtful exchange. Join the conversation.</p>
      </div>
      <div class="hero-rule"></div>
    </section>

    <div class="page-wrap">
      <!-- Comment form (authenticated) -->
      <Transition name="slide-up">
        <div v-if="auth.isAuthenticated" class="section-form">
          <CommentForm @submitted="onNewComment" />
        </div>
        <div v-else class="auth-nudge">
          <span>Want to join the conversation?</span>
          <RouterLink to="/login" class="auth-nudge-link">Sign in</RouterLink>
          <span>or</span>
          <RouterLink to="/register" class="auth-nudge-link auth-nudge-link--join">Create account</RouterLink>
        </div>
      </Transition>

      <!-- Controls -->
      <div class="list-controls">
        <div class="ws-status">
          <span v-if="reconnecting" class="ws-dot ws-dot--reconnecting" title="Reconnecting…"></span>
          <span v-else-if="connected" class="ws-dot ws-dot--live" title="Live updates on"></span>
          <span v-else class="ws-dot ws-dot--off" title="Offline"></span>
          <span class="ws-label">{{ reconnecting ? 'Reconnecting…' : connected ? 'Live' : 'Offline' }}</span>
        </div>
        <div class="list-count">
          <span v-if="!store.loading">{{ store.pagination.count }} comment{{ store.pagination.count !== 1 ? 's' : '' }}</span>
        </div>
        <div class="sort-wrap">
          <span class="sort-label">Sort by</span>
          <select class="sort-select" v-model="ordering" @change="applySort">
            <option value="-created_at">Newest first</option>
            <option value="created_at">Oldest first</option>
            <option value="user__username">Username A–Z</option>
            <option value="-user__username">Username Z–A</option>
            <option value="user__email">Email A–Z</option>
          </select>
        </div>
      </div>

      <!-- Comment list -->
      <div class="comment-list">
        <div v-if="store.loading" class="list-loader">
          <div class="loader-dots">
            <span></span><span></span><span></span>
          </div>
        </div>

        <template v-else-if="store.comments.length">
          <TransitionGroup name="comment-list" tag="div">
            <CommentCard
              v-for="comment in store.comments"
              :key="comment.id"
              :comment="comment"
              @deleted="onDeleted"
              @replied="onReplied"
            />
          </TransitionGroup>
        </template>

        <div v-else class="list-empty">
          <div class="empty-icon">✦</div>
          <p>No comments yet. Be the first!</p>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="store.currentPage === 1"
          @click="goToPage(store.currentPage - 1)"
        >← Prev</button>

        <div class="page-numbers">
          <button
            v-for="p in pageNumbers"
            :key="p"
            class="page-num"
            :class="{ active: p === store.currentPage, ellipsis: p === '…' }"
            :disabled="p === '…'"
            @click="p !== '…' && goToPage(p)"
          >{{ p }}</button>
        </div>

        <button
          class="page-btn"
          :disabled="store.currentPage === totalPages"
          @click="goToPage(store.currentPage + 1)"
        >Next →</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useCommentsStore } from '../stores/comments.js'
import CommentForm from '../components/CommentForm.vue'
import CommentCard from '../components/CommentCard.vue'
import { useCommentSocket } from '../composables/useCommentSocket.js'

const auth = useAuthStore()
const store = useCommentsStore()
const ordering = ref('-created_at')

onMounted(() => store.fetchComments(1, ordering.value))
const { connected, reconnecting } = useCommentSocket()

function applySort() {
  store.fetchComments(1, ordering.value)
}

function goToPage(page) {
  store.fetchComments(page, ordering.value)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onNewComment() {
  store.fetchComments(1, ordering.value)
}

function onDeleted() {
  store.fetchComments(store.currentPage, ordering.value)
}

function onReplied() {
  store.fetchComments(store.currentPage, ordering.value)
}

const totalPages = computed(() => Math.ceil(store.pagination.count / 25))

const pageNumbers = computed(() => {
  const curr = store.currentPage
  const total = totalPages.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  if (curr <= 4) {
    pages.push(1, 2, 3, 4, 5, '…', total)
  } else if (curr >= total - 3) {
    pages.push(1, '…', total-4, total-3, total-2, total-1, total)
  } else {
    pages.push(1, '…', curr-1, curr, curr+1, '…', total)
  }
  return pages
})
</script>

<style scoped>
.home { min-height: 100vh; }

/* Hero */
.hero {
  padding: 60px 24px 0;
  max-width: 900px;
  margin: 0 auto;
}
.hero-inner { text-align: center; padding-bottom: 40px; }

.hero-label {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 16px;
  padding: 4px 12px;
  border: 1px solid var(--border-strong);
  border-radius: 20px;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(48px, 8vw, 80px);
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -2px;
  line-height: 1;
  margin-bottom: 16px;
}

.hero-sub {
  font-size: 16px;
  color: var(--ink-light);
  font-weight: 300;
  letter-spacing: 0.3px;
}

.hero-rule {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-strong), transparent);
}

/* Page wrap */
.page-wrap {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 24px 60px;
}

/* Form section */
.section-form { padding: 40px 0 32px; }

.auth-nudge {
  padding: 32px 0;
  text-align: center;
  font-size: 14px;
  color: var(--ink-light);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.auth-nudge-link {
  font-weight: 700;
  padding: 6px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border-strong);
  color: var(--ink);
  transition: all 0.15s;
  text-decoration: none;
}
.auth-nudge-link:hover { background: var(--paper-dark); }
.auth-nudge-link--join { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.auth-nudge-link--join:hover { background: var(--accent); border-color: var(--accent); }

/* Controls */
.list-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 0;
}

.list-count {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--ink-faint);
  text-transform: uppercase;
}

.sort-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.sort-select {
  font-family: var(--font-body);
  font-size: 12px;
  padding: 5px 10px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--paper);
  color: var(--ink);
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s;
}
.sort-select:focus { border-color: var(--ink); }

/* Comment list */
.comment-list { padding: 0; }

.comment-list-enter-active { transition: all 0.3s ease; }
.comment-list-enter-from { opacity: 0; transform: translateY(10px); }

/* Loader */
.list-loader {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

.loader-dots {
  display: flex;
  gap: 8px;
  align-items: center;
}
.loader-dots span {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--ink-faint);
  animation: dotPulse 1.2s ease-in-out infinite;
}
.loader-dots span:nth-child(2) { animation-delay: 0.2s; }
.loader-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
  0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* Empty */
.list-empty {
  padding: 80px 0;
  text-align: center;
  color: var(--ink-faint);
}
.empty-icon {
  font-size: 32px;
  margin-bottom: 12px;
  opacity: 0.3;
}
.list-empty p { font-size: 14px; }

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0 0;
}

.page-btn {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 7px 16px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: transparent;
  color: var(--ink-light);
  cursor: pointer;
  transition: all 0.15s;
}
.page-btn:hover:not(:disabled) { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.page-numbers { display: flex; gap: 4px; }

.page-num {
  width: 34px; height: 34px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  color: var(--ink-light);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  display: flex; align-items: center; justify-content: center;
}
.page-num:hover:not(.active):not(.ellipsis) { background: var(--paper-dark); }
.page-num.active { background: var(--ink); color: var(--paper); border-color: var(--ink); }
.page-num.ellipsis { border: none; cursor: default; color: var(--ink-faint); }

/* WebSocket status */
.ws-status {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ws-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ws-dot--live {
  background: var(--teal);
  box-shadow: 0 0 0 2px rgba(42,122,110,0.2);
  animation: pulse-live 2.5s ease-in-out infinite;
}
.ws-dot--reconnecting {
  background: var(--gold);
  animation: pulse-live 0.8s ease-in-out infinite;
}
.ws-dot--off {
  background: var(--ink-faint);
}
@keyframes pulse-live {
  0%, 100% { box-shadow: 0 0 0 2px rgba(42,122,110,0.2); }
  50% { box-shadow: 0 0 0 5px rgba(42,122,110,0); }
}
.ws-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--ink-faint);
}

</style>