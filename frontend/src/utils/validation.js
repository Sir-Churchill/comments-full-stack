const ALLOWED_TAGS = ['a', 'code', 'i', 'strong']

// Strictly allowed attributes per tag — nothing else permitted.
const ALLOWED_ATTRS = {
  a: ['href', 'title'],
  // code, i, strong: no attributes allowed
}

// Safe value patterns per attribute.
// href must be http/https/mailto — blocks javascript: and data: URIs.
const SAFE_ATTR_VALUE = {
  href:  /^(https?:\/\/|mailto:)[^\s"'<>]*$/i,
  title: /^[^<>"]*$/,
}

/**
 * Parse raw attribute string into { name: value } map.
 * Handles quoted and unquoted values.
 */
function parseAttrs(attrStr) {
  const result = {}
  const re = /([a-zA-Z][a-zA-Z0-9\-]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]*)))?/g
  let m
  while ((m = re.exec(attrStr)) !== null) {
    const name = m[1].toLowerCase()
    const value = (m[2] ?? m[3] ?? m[4] ?? '').trim()
    result[name] = value
  }
  return result
}

/**
 * Validate a tag's attributes against the allow-list.
 * Returns error string or null.
 */
function validateAttrs(tagName, attrStr) {
  const allowed = ALLOWED_ATTRS[tagName] || []
  const attrs = parseAttrs(attrStr)

  for (const [name, value] of Object.entries(attrs)) {
    if (!allowed.includes(name)) {
      return `Attribute "${name}" is not allowed on <${tagName}>.`
    }
    const pattern = SAFE_ATTR_VALUE[name]
    if (pattern && !pattern.test(value)) {
      return `Unsafe value for attribute "${name}" on <${tagName}>.`
    }
  }

  if (allowed.length === 0 && Object.keys(attrs).length > 0) {
    return `Tag <${tagName}> must not have any attributes.`
  }

  return null
}

/**
 * Strip all HTML tags and return plain text.
 */
function stripTags(str) {
  return str.replace(/<[^>]*>/g, '')
}

/**
 * Full client-side validation of user HTML input.
 *
 * Checks:
 *   1. Only allowed tags are used
 *   2. No dangerous attributes / event handlers / javascript: hrefs
 *   3. Tags are properly nested and closed (XHTML-valid)
 *   4. Visible text content is not empty after stripping tags
 *
 * Returns { valid: boolean, error: string|null }
 */
export function validateHtml(text) {
  let m

  // ── 1 & 2: scan every opening tag for forbidden names and bad attributes ──
  const openTagRe = /<([a-zA-Z][a-zA-Z0-9]*)([^>]*)>/g
  while ((m = openTagRe.exec(text)) !== null) {
    const tagName = m[1].toLowerCase()
    const attrStr = m[2]

    if (!ALLOWED_TAGS.includes(tagName)) {
      return { valid: false, error: `Tag <${tagName}> is not allowed. Allowed: ${ALLOWED_TAGS.join(', ')}` }
    }

    const attrError = validateAttrs(tagName, attrStr)
    if (attrError) return { valid: false, error: attrError }
  }

  // ── 3: nesting / closing balance check ────────────────────────────────────
  const tagRe = /<(\/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>/g
  const stack = []
  while ((m = tagRe.exec(text)) !== null) {
    const closing = m[1]
    const tag = m[2].toLowerCase()
    const attrStr = m[3]
    if (!ALLOWED_TAGS.includes(tag)) continue

    if (!closing) {
      if (attrStr.trimEnd().endsWith('/')) continue // self-closing
      stack.push(tag)
    } else {
      if (stack.length === 0 || stack[stack.length - 1] !== tag) {
        return { valid: false, error: `Unexpected closing tag </${tag}>` }
      }
      stack.pop()
    }
  }

  if (stack.length > 0) {
    return { valid: false, error: `Unclosed tag: <${stack[stack.length - 1]}>` }
  }

  // ── 4: non-empty visible content ──────────────────────────────────────────
  const visibleText = stripTags(text).trim()
  if (!visibleText) {
    return { valid: false, error: 'Message must contain visible text, not only tags.' }
  }

  return { valid: true, error: null }
}

/**
 * Resize image file to max 320x240 proportionally. Returns a File/Blob.
 */
export function resizeImage(file, maxW = 320, maxH = 240) {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    img.onload = () => {
      URL.revokeObjectURL(url)
      let { width, height } = img
      if (width <= maxW && height <= maxH) {
        resolve(file)
        return
      }
      const ratio = Math.min(maxW / width, maxH / height)
      width = Math.round(width * ratio)
      height = Math.round(height * ratio)

      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)

      const mime = file.type || 'image/jpeg'
      canvas.toBlob((blob) => {
        resolve(new File([blob], file.name, { type: mime }))
      }, mime, 0.92)
    }
    img.onerror = reject
    img.src = url
  })
}

export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
export const MAX_TXT_SIZE = 100 * 1024

export function validateImageFile(file) {
  if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
    return 'Only JPG, PNG and GIF images are allowed.'
  }
  return null
}

export function validateTxtFile(file) {
  if (!file.name.endsWith('.txt')) return 'Only .txt files are allowed.'
  if (file.size > MAX_TXT_SIZE) return `File must be under 100 KB (got ${(file.size/1024).toFixed(1)} KB).`
  return null
}