<template>
  <article class="comment-card" :class="{ 'comment-card--child': depth > 0 }">
    <!-- Header -->
    <header class="cc-header">
      <div class="cc-avatar" :style="{ background: avatarColor }">
        {{ initials }}
      </div>
      <div class="cc-meta">
        <span class="cc-username">{{ comment.user_name }}</span>
        <a v-if="comment.home_page" :href="comment.home_page" target="_blank" class="cc-homepage" rel="noopener">
          ↗ {{ cleanUrl(comment.home_page) }}
        </a>
        <time class="cc-time" :title="fullDate">{{ relativeDate }}</time>
      </div>

      <div class="cc-actions">
        <!-- Collapse toggle (only if has children) -->
        <button
          v-if="hasChildren"
          class="cc-btn cc-btn--collapse"
          :class="{ collapsed: isCollapsed }"
          :title="isCollapsed ? 'Expand replies' : 'Collapse replies'"
          @click="isCollapsed = !isCollapsed"
        >
          <span class="collapse-icon">{{ isCollapsed ? '▶' : '▼' }}</span>
          <span class="collapse-count">{{ totalChildCount }}</span>
        </button>

        <!-- Reply -->
        <button
          class="cc-btn"
          :class="{ active: showReply }"
          @click="handleReplyClick"
        >↩ Reply</button>

        <!-- Delete -->
        <button
          v-if="auth.user?.id === comment.user_id || auth.user?.is_staff"
          class="cc-btn cc-btn--danger"
          @click="handleDelete"
        >✕</button>
      </div>
    </header>

    <!-- Body -->
    <div class="cc-body">
      <div class="cc-text" v-html="comment.text"></div>

      <div v-if="comment.image" class="cc-attachment">
        <img
          :src="comment.image"
          class="cc-image"
          alt="attachment"
          @click="openLightbox(comment.image)"
          title="Click to enlarge"
        />
      </div>

      <div v-if="comment.file" class="cc-file">
        <a :href="comment.file" target="_blank" class="cc-file-link" rel="noopener">
          📄 <span>{{ fileName(comment.file) }}</span>
        </a>
      </div>
    </div>

    <!-- Reply form -->
    <Transition name="slide-up">
      <div v-if="showReply" class="cc-reply-form">
        <CommentForm
          :parent-id="comment.id"
          :is-reply="true"
          @submitted="onReplied"
          @cancel="showReply = false"
        />
      </div>
    </Transition>

    <!-- Children with collapse -->
    <Transition name="tree-collapse">
      <div
        v-if="hasChildren && !isCollapsed"
        class="cc-children"
      >
        <CommentCard
          v-for="child in comment.children"
          :key="child.id"
          :comment="child"
          :depth="depth + 1"
          @deleted="$emit('deleted', $event)"
          @replied="$emit('replied', $event)"
        />
      </div>
    </Transition>

    <!-- Collapsed indicator -->
    <Transition name="fade">
      <div
        v-if="hasChildren && isCollapsed"
        class="cc-collapsed-bar"
        @click="isCollapsed = false"
      >
        <span>{{ totalChildCount }} repl{{ totalChildCount === 1 ? 'y' : 'ies' }} hidden</span>
        <span class="cc-expand-hint">click to expand</span>
      </div>
    </Transition>
  </article>

  <!-- Lightbox -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div v-if="lightboxSrc" class="lightbox" @click.self="lightboxSrc = null">
        <button class="lightbox-close" @click="lightboxSrc = null">✕</button>
        <div class="lightbox-inner">
          <img :src="lightboxSrc" class="lightbox-img" alt="Full size" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useCommentsStore } from '../stores/comments.js'
import CommentForm from './CommentForm.vue'

const props = defineProps({
  comment: { type: Object, required: true },
  depth: { type: Number, default: 0 },
})
const emit = defineEmits(['deleted', 'replied'])

const auth = useAuthStore()
const store = useCommentsStore()
const router = useRouter()

const showReply = ref(false)
const lightboxSrc = ref(null)
const isCollapsed = ref(false)

const hasChildren = computed(() => props.comment.children && props.comment.children.length > 0)

// Recursively count all descendants
function countDescendants(children) {
  if (!children?.length) return 0
  return children.reduce((acc, c) => acc + 1 + countDescendants(c.children), 0)
}
const totalChildCount = computed(() => countDescendants(props.comment.children))

const initials = computed(() => (props.comment.user_name || '?').slice(0, 2).toUpperCase())

const avatarColor = computed(() => {
  let hash = 0
  for (const c of (props.comment.user_name || '')) hash = c.charCodeAt(0) + ((hash << 5) - hash)
  const colors = ['#c8433a','#2a7a6e','#b8860b','#5a6e8a','#7a5a6e','#4a7a5a']
  return colors[Math.abs(hash) % colors.length]
})

const relativeDate = computed(() => {
  const d = new Date(props.comment.created_at)
  const diff = Date.now() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric' })
})

const fullDate = computed(() => new Date(props.comment.created_at).toLocaleString())

function cleanUrl(url) {
  return url.replace(/^https?:\/\//, '').replace(/\/$/, '')
}

function fileName(url) {
  return url.split('/').pop()
}

function openLightbox(src) {
  lightboxSrc.value = src
}

function handleReplyClick() {
  if (!auth.isAuthenticated) {
    router.push('/login')
    return
  }
  showReply.value = !showReply.value
}

async function handleDelete() {
  if (!confirm('Delete this comment?')) return
  await store.deleteComment(props.comment.id)
  emit('deleted', props.comment.id)
}

function onReplied(newComment) {
  showReply.value = false
  emit('replied', newComment)
}
</script>

<style scoped>
.comment-card {
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
  animation: fadeInUp 0.3s ease both;
}
.comment-card:last-child { border-bottom: none; }
.comment-card--child { padding: 14px 0 0; border-bottom: none; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Header */
.cc-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.cc-avatar {
  width: 36px; height: 36px;
  border-radius: 50%;
  color: white;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.cc-meta {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
}

.cc-username { font-size: 14px; font-weight: 700; color: var(--ink); }

.cc-homepage { font-size: 11px; color: var(--teal); text-decoration: none; }
.cc-homepage:hover { text-decoration: underline; }

.cc-time { font-size: 11px; color: var(--ink-faint); margin-left: auto; }

.cc-actions {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
  align-items: center;
}

.cc-btn {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 4px 10px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition: all 0.15s;
}
.cc-btn:hover, .cc-btn.active {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}
.cc-btn--danger:hover { background: var(--accent); border-color: var(--accent); color: white; }

/* Collapse button */
.cc-btn--collapse {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  color: var(--teal);
  border-color: rgba(42,122,110,0.3);
  font-size: 10px;
}
.cc-btn--collapse:hover {
  background: var(--teal);
  border-color: var(--teal);
  color: white;
}
.cc-btn--collapse.collapsed {
  background: rgba(42,122,110,0.08);
  color: var(--teal);
}

.collapse-icon { font-size: 9px; transition: transform 0.2s; }
.collapse-count {
  background: rgba(42,122,110,0.15);
  color: var(--teal);
  border-radius: 10px;
  padding: 0 5px;
  font-size: 10px;
  font-weight: 700;
}
.cc-btn--collapse:hover .collapse-count { background: rgba(255,255,255,0.2); color: white; }

/* Body */
.cc-body { padding-left: 48px; }

.cc-text {
  font-size: 14px;
  line-height: 1.75;
  color: var(--ink);
  margin-bottom: 10px;
  word-break: break-word;
}
.cc-text :deep(a) { color: var(--accent); text-decoration: underline; }
.cc-text :deep(code) {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--paper-dark);
  padding: 2px 6px;
  border-radius: 2px;
  border: 1px solid var(--border);
}
.cc-text :deep(strong) { font-weight: 700; }
.cc-text :deep(i) { font-style: italic; color: var(--ink-light); }

.cc-attachment { margin: 10px 0; }
.cc-image {
  max-width: 320px;
  max-height: 240px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  cursor: zoom-in;
  transition: all 0.2s;
  display: block;
}
.cc-image:hover { transform: scale(1.02); box-shadow: var(--shadow-md); border-color: var(--border-strong); }

.cc-file { margin: 8px 0; }
.cc-file-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--teal);
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--paper-warm);
  transition: all 0.15s;
  text-decoration: none;
}
.cc-file-link:hover { background: var(--teal); color: white; border-color: var(--teal); }

/* Reply form */
.cc-reply-form { padding-left: 48px; margin-top: 14px; }

/* Children */
.cc-children {
  padding-left: 36px;
  margin-top: 4px;
  border-left: 2px solid var(--border);
}

/* Collapsed bar */
.cc-collapsed-bar {
  margin-left: 48px;
  margin-top: 8px;
  padding: 6px 12px;
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--ink-faint);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.15s;
  background: var(--paper-warm);
}
.cc-collapsed-bar:hover { border-color: var(--teal); color: var(--teal); background: rgba(42,122,110,0.04); }
.cc-expand-hint { font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; opacity: 0.6; }

/* Tree collapse animation */
.tree-collapse-enter-active { transition: all 0.25s ease; overflow: hidden; }
.tree-collapse-leave-active { transition: all 0.2s ease; overflow: hidden; }
.tree-collapse-enter-from { opacity: 0; max-height: 0; transform: translateY(-4px); }
.tree-collapse-leave-to { opacity: 0; max-height: 0; }
.tree-collapse-enter-to, .tree-collapse-leave-from { max-height: 2000px; }

/* Lightbox */
.lightbox {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(10, 8, 6, 0.9);
  display: flex; align-items: center; justify-content: center;
  cursor: zoom-out;
}
.lightbox-close {
  position: absolute; top: 20px; right: 20px;
  width: 40px; height: 40px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  background: transparent;
  color: rgba(255,255,255,0.7);
  font-size: 16px; cursor: pointer;
  transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.lightbox-close:hover { background: rgba(255,255,255,0.1); color: white; }
.lightbox-inner { max-width: 90vw; max-height: 90vh; }
.lightbox-img {
  max-width: 100%; max-height: 90vh;
  object-fit: contain;
  border-radius: var(--radius);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.lightbox-enter-active { transition: all 0.25s ease; }
.lightbox-leave-active { transition: all 0.2s ease; }
.lightbox-enter-from, .lightbox-leave-to { opacity: 0; }
</style>