import { defineStore } from 'pinia'
import { ref } from 'vue'
import { commentsApi, captchaApi } from '../api/index.js'

export const useCommentsStore = defineStore('comments', () => {
  const comments = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({ count: 0, next: null, previous: null })
  const currentPage = ref(1)
  const ordering = ref('-created_at')

  async function fetchComments(page = 1, order = ordering.value) {
    loading.value = true
    error.value = null
    ordering.value = order
    currentPage.value = page
    try {
      const { data } = await commentsApi.list({ page, ordering: order })
      comments.value = data.results
      pagination.value = { count: data.count, next: data.next, previous: data.previous }
    } catch (e) {
      error.value = 'Failed to load comments'
    } finally {
      loading.value = false
    }
  }

  async function createComment(payload) {
    const { data } = await commentsApi.create(payload)
    return data
  }

  async function deleteComment(id) {
    await commentsApi.delete(id)
    comments.value = comments.value.filter(c => c.id !== id)
  }

  async function getCaptcha() {
    const { data } = await captchaApi.get()
    return data
  }

  return { comments, loading, error, pagination, currentPage, ordering, fetchComments, createComment, deleteComment, getCaptcha }
})