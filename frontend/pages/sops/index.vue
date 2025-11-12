<script setup lang="ts">
const { get } = useApi()

type Row = Record<string, any>
const rows = ref<Row[]>([])
const loading = ref(true)
const err = ref<string | null>(null)

// inline video preview modal
const previewOpen = ref(false)
const previewTitle = ref('')
const previewSrc = ref('')

onMounted(load)

async function load() {
  loading.value = true; err.value = null
  try {
    const data:any = await get('/sops/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e:any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load')
  } finally {
    loading.value = false
  }
}

/** Extract best source fields by common names */
function getSource(r: Row) {
  // adjust/order as needed; first non-empty wins
  const video = r.video_url || r.video || r.media_url || ''
  const pdf = r.pdf_url || r.pdf || ''
  const pptx = r.pptx_url || r.pptx || ''
  const link = r.link_url || r.link || ''
  const title = r.title || r.name || r.code || r.id
  return { video, pdf, pptx, link, title }
}

function openItem(r: Row) {
  const { video, pdf, pptx, link, title } = getSource(r)
  const first = [video, pdf, pptx, link].find(Boolean) || ''
  if (!first) return

  const lower = String(first).toLowerCase()

  // videos: inline modal
  if (lower.endsWith('.mp4') || lower.endsWith('.webm') || lower.includes('youtube.com') || lower.includes('vimeo.com')) {
    // simple direct mp4/webm player; for YouTube/Vimeo you might swap to iframe embed later
    previewTitle.value = String(title)
    previewSrc.value = String(first)
    previewOpen.value = true
    return
  }

  // pdfs: route to viewer so heartbeat works
  if (lower.endsWith('.pdf')) {
    navigateTo(`/sops/${r.id}?type=pdf&src=${encodeURIComponent(String(first))}`)
    return
  }

  // everything else (pptx/links): open new tab
  window.open(String(first), '_blank', 'noopener')
}

// helper: produce a user-friendly “type” label
function kind(r: Row) {
  const { video, pdf, pptx, link } = getSource(r)
  if (video) return 'Video'
  if (pdf) return 'PDF'
  if (pptx) return 'PPTX'
  if (link) return 'Link'
  return 'Unknown'
}
function absoluteMediaUrl(pathOrUrl: string) {
  if (!pathOrUrl) return ''
  try {
    // already absolute?
    new URL(pathOrUrl)
    return pathOrUrl
  } catch {
    // join with backend origin
    const api = useApi().baseURL
    const origin = new URL(api).origin
    if (pathOrUrl.startsWith('/')) return origin + pathOrUrl
    return origin.replace(/\/+$/, '') + '/' + pathOrUrl.replace(/^\/+/, '')
  }
}
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold">SOPs</h1>

    <div v-if="loading" class="text-gray-500">Loading…</div>
    <div v-else-if="err" class="text-red-600 break-all">{{ err }}</div>

    <ul v-else class="space-y-2">
      <li v-for="r in rows" :key="r.id" class="border rounded p-3 flex items-center gap-4">
        <div class="flex-1 min-w-0">
          <div class="font-medium truncate">
            {{ r.title || r.name || r.code || r.id }}
          </div>
          <div class="text-xs text-gray-600 truncate">
            {{ r.description || r.summary || '' }}
          </div>
          <div class="text-xs text-gray-500 mt-1">{{ kind(r) }}</div>
        </div>
        <button class="px-3 py-1 rounded bg-black text-white" @click="openItem(r)">
          Open
        </button>
      </li>
    </ul>

    <!-- Inline video preview -->
    <div v-if="previewOpen" class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div class="bg-white rounded shadow max-w-4xl w-full p-3 space-y-2">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold">{{ previewTitle }}</h3>
          <button class="text-sm border rounded px-2 py-1" @click="previewOpen=false">Close</button>
        </div>
        <video :src="previewSrc" controls class="w-full rounded border" />
      </div>
    </div>
  </div>
</template>
