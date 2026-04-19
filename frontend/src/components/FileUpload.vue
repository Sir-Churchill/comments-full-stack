<template>
  <div class="file-upload">
    <div class="file-tabs">
      <button
        type="button"
        class="file-tab"
        :class="{ active: mode === 'image' }"
        @click="setMode('image')"
      >🖼 Image</button>
      <button
        type="button"
        class="file-tab"
        :class="{ active: mode === 'file' }"
        @click="setMode('file')"
      >📄 Text file</button>
      <button
        v-if="hasFile"
        type="button"
        class="file-tab file-tab--remove"
        @click="removeFile"
      >✕ Remove</button>
    </div>

    <div class="file-body">
      <!-- Image mode -->
      <template v-if="mode === 'image'">
        <div
          class="dropzone"
          :class="{ dragover: isDragging, 'has-file': imagePreview }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.imageInput.click()"
        >
          <template v-if="imagePreview">
            <img :src="imagePreview" class="dropzone-preview" alt="preview" />
            <div class="dropzone-overlay">
              <span>Change image</span>
            </div>
          </template>
          <template v-else>
            <div class="dropzone-icon">⬆</div>
            <div class="dropzone-text">Drop image or <u>browse</u></div>
            <div class="dropzone-sub">JPG, PNG, GIF · Will resize to 320×240 if needed</div>
          </template>
        </div>
        <input
          ref="imageInput"
          type="file"
          accept="image/jpeg,image/png,image/gif"
          style="display:none"
          @change="handleImageChange"
        />
        <div v-if="resizing" class="file-status">
          <span class="spinner"></span> Resizing image…
        </div>
        <div v-if="imageMeta" class="file-meta">
          {{ imageMeta }}
        </div>
      </template>

      <!-- File mode -->
      <template v-if="mode === 'file'">
        <div
          class="dropzone dropzone--file"
          :class="{ dragover: isDragging, 'has-file': txtFile }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleFileDrop"
          @click="$refs.fileInput.click()"
        >
          <template v-if="txtFile">
            <div class="dropzone-icon">📄</div>
            <div class="dropzone-filename">{{ txtFile.name }}</div>
            <div class="dropzone-sub">{{ (txtFile.size / 1024).toFixed(1) }} KB</div>
          </template>
          <template v-else>
            <div class="dropzone-icon">📂</div>
            <div class="dropzone-text">Drop .txt file or <u>browse</u></div>
            <div class="dropzone-sub">Plain text only · Max 100 KB</div>
          </template>
        </div>
        <input
          ref="fileInput"
          type="file"
          accept=".txt,text/plain"
          style="display:none"
          @change="handleFileChange"
        />
      </template>
    </div>

    <Transition name="slide-up">
      <div v-if="error" class="file-error">⚠ {{ error }}</div>
    </Transition>
  </div>

  <!-- Lightbox -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div v-if="lightboxOpen" class="lightbox" @click.self="lightboxOpen = false">
        <button class="lightbox-close" @click="lightboxOpen = false">✕</button>
        <div class="lightbox-content">
          <img :src="imagePreview" class="lightbox-img" alt="Full size" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { validateImageFile, validateTxtFile, resizeImage } from '../utils/validation.js'

const emit = defineEmits(['update:image', 'update:file'])

const mode = ref('image')
const isDragging = ref(false)
const imagePreview = ref(null)
const imageFile = ref(null)
const txtFile = ref(null)
const error = ref(null)
const resizing = ref(false)
const lightboxOpen = ref(false)
const imageMeta = ref(null)

const hasFile = computed(() => imageFile.value || txtFile.value)

function setMode(m) {
  mode.value = m
  error.value = null
}

function removeFile() {
  imageFile.value = null
  imagePreview.value = null
  txtFile.value = null
  imageMeta.value = null
  error.value = null
  emit('update:image', null)
  emit('update:file', null)
}

async function processImage(file) {
  error.value = null
  const err = validateImageFile(file)
  if (err) { error.value = err; return }

  resizing.value = true
  try {
    const processed = await resizeImage(file, 320, 240)
    imageFile.value = processed

    // Generate preview
    const reader = new FileReader()
    reader.onload = (e) => {
      imagePreview.value = e.target.result
      // Show dimensions
      const img = new Image()
      img.onload = () => {
        imageMeta.value = `${img.width} × ${img.height}px · ${(processed.size / 1024).toFixed(1)} KB`
        if (processed !== file) imageMeta.value += ' (resized)'
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(processed)
    emit('update:image', processed)
  } finally {
    resizing.value = false
  }
}

function handleImageChange(e) {
  const file = e.target.files[0]
  if (file) processImage(file)
  e.target.value = ''
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) processImage(file)
}

function processFile(file) {
  error.value = null
  const err = validateTxtFile(file)
  if (err) { error.value = err; return }
  txtFile.value = file
  emit('update:file', file)
}

function handleFileChange(e) {
  const file = e.target.files[0]
  if (file) processFile(file)
  e.target.value = ''
}

function handleFileDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) processFile(file)
}

// Expose lightbox open for parent (image click in comment list)
defineExpose({ openLightbox: () => { if (imagePreview.value) lightboxOpen.value = true } })
</script>

<style scoped>
.file-upload { display: flex; flex-direction: column; gap: 0; }

.file-tabs {
  display: flex;
  gap: 2px;
  margin-bottom: 8px;
}

.file-tab {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 5px 14px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius) var(--radius) 0 0;
  background: var(--paper-warm);
  color: var(--ink-faint);
  cursor: pointer;
  transition: all 0.15s;
}
.file-tab:hover { color: var(--ink); background: var(--paper-dark); }
.file-tab.active { background: var(--paper); color: var(--ink); border-bottom-color: var(--paper); }
.file-tab--remove { margin-left: auto; color: var(--accent); border-color: var(--accent-muted); }
.file-tab--remove:hover { background: var(--accent); color: white; border-color: var(--accent); }

.file-body {
  border: 1px solid var(--border-strong);
  border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md);
  overflow: hidden;
}

.dropzone {
  padding: 28px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--paper);
  position: relative;
  overflow: hidden;
}
.dropzone:hover { background: var(--paper-warm); }
.dropzone.dragover { background: rgba(42,122,110,0.06); border-color: var(--teal); }
.dropzone.has-file { padding: 12px; }

.dropzone-icon { font-size: 28px; margin-bottom: 8px; opacity: 0.5; }
.dropzone-text { font-size: 14px; color: var(--ink-light); }
.dropzone-text u { color: var(--accent); }
.dropzone-sub { font-size: 11px; color: var(--ink-faint); margin-top: 4px; }
.dropzone-filename { font-family: var(--font-mono); font-size: 13px; color: var(--ink); margin: 4px 0; }

.dropzone-preview {
  max-width: 100%;
  max-height: 160px;
  object-fit: contain;
  border-radius: var(--radius);
  display: block;
  margin: 0 auto;
  transition: transform 0.2s;
}
.dropzone-preview:hover { transform: scale(1.02); }

.dropzone-overlay {
  position: absolute;
  inset: 0;
  background: rgba(26,20,16,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
  opacity: 0;
  transition: opacity 0.2s;
}
.dropzone:hover .dropzone-overlay { opacity: 1; }

.file-meta {
  padding: 6px 12px;
  font-size: 11px;
  color: var(--ink-faint);
  font-family: var(--font-mono);
  background: var(--paper-warm);
  border-top: 1px solid var(--border);
}

.file-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--ink-light);
  background: var(--paper-warm);
  border-top: 1px solid var(--border);
}

.spinner {
  width: 12px; height: 12px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

.file-error {
  padding: 8px 12px;
  font-size: 12px;
  color: var(--accent-dark);
  background: #fdf0ef;
  border: 1px solid var(--accent-muted);
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
}

/* Lightbox */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(10, 8, 6, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}
.lightbox-close {
  position: absolute;
  top: 20px; right: 20px;
  width: 40px; height: 40px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  background: transparent;
  color: rgba(255,255,255,0.7);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.lightbox-close:hover { background: rgba(255,255,255,0.1); color: white; }
.lightbox-content {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-img {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--radius);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}

.lightbox-enter-active { transition: all 0.25s ease; }
.lightbox-leave-active { transition: all 0.2s ease; }
.lightbox-enter-from, .lightbox-leave-to { opacity: 0; }
.lightbox-enter-from .lightbox-img { transform: scale(0.9); }
</style>