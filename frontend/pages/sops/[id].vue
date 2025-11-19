<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const sopId = computed(() => String(route.params.id || ''))

type Sop = {
  id: string
  title?: string | null
  code?: string | null
  description?: string | null
  media_url?: string | null
  // other fields may exist on the model, but we don't rely on them
  created_at?: string | null
}

type SopView = {
  id: number
  sop: string
  seconds_viewed: number
  pages_viewed: number
  progress: number
  completed: boolean
  last_heartbeat?: string | null
}

const loading = ref(true)
const err = ref<string | null>(null)

const sop = ref<Sop | null>(null)
const view = ref<SopView | null>(null)
const markingComplete = ref(false)

onMounted(load)

async function load () {
  if (!sopId.value) {
    err.value = 'No SOP id provided in route.'
    return
  }

  loading.value = true
  err.value = null
  sop.value = null
  view.value = null

  try {
    // 1) Load the SOP itself
    const sopData: any = await get(`/sops/${sopId.value}/`)
    sop.value = sopData

    // 2) Try to find any existing SOPView for this SOP
    //    (we use /me/sop-views/ and filter client-side)
    const allViews: any = await get('/me/sop-views/')
    const list = Array.isArray(allViews) ? allViews : (allViews.results || [])
    const existing = list.find((v: any) => v.sop === sopId.value)
    if (existing) {
      view.value = existing
    }
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load SOP')
  } finally {
    loading.value = false
  }
}

const mediaUrl = computed(() => sop.value?.media_url || '')

const isVideo = computed(() => {
  if (!mediaUrl.value) return false
  const lower = mediaUrl.value.toLowerCase()
  return lower.endsWith('.mp4') || lower.endsWith('.webm') || lower.endsWith('.mov')
})

const isPdf = computed(() => {
  if (!mediaUrl.value) return false
  return mediaUrl.value.toLowerCase().endsWith('.pdf')
})

const isCompleted = computed(() => !!view.value?.completed)

function createdLabel (value?: string | null) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString()
}

async function markAsViewed () {
  if (!sopId.value) return
  markingComplete.value = true
  err.value = null

  try {
    const payload = {
      completed: true,
      progress: 1,
    }
    const data: any = await post(`/sops/${sopId.value}/view/`, payload)
    // Heartbeat returns the SOPView record, update local state
    view.value = data
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to mark SOP as viewed')
  } finally {
    markingComplete.value = false
  }
}

function goBack () {
  // Simple back behaviour; fallback to /sops
  if (window.history.length > 1) window.history.back()
  else router.push('/sops')
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          {{ sop?.title || 'SOP' }}
        </h1>
        <p class="text-sm text-gray-600">
          Standard operating procedure details and training media.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="goBack"
        >
          Back
        </button>

        <button
          v-if="!isCompleted"
          type="button"
          class="px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
          :disabled="markingComplete"
          @click="markAsViewed"
        >
          <span v-if="!markingComplete">Mark as viewed</span>
          <span v-else>Saving…</span>
        </button>

        <span
          v-else
          class="inline-flex items-center px-3 py-1.5 text-xs rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"
        >
          ✅ SOP viewed and recorded
        </span>
      </div>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading SOP…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else-if="sop" class="space-y-6">
      <!-- Meta / description -->
      <section class="bg-white rounded-xl shadow-sm border p-4 space-y-2">
        <div class="flex flex-wrap gap-3 text-sm text-gray-600">
          <div v-if="sop.code">
            <span class="font-semibold">Code:</span>
            <span class="ml-1">{{ sop.code }}</span>
          </div>
          <div v-if="sop.created_at">
            <span class="font-semibold">Created:</span>
            <span class="ml-1">{{ createdLabel(sop.created_at) }}</span>
          </div>
          <div v-if="view">
            <span class="font-semibold">Progress:</span>
            <span class="ml-1">
              {{ Math.round((view.progress || 0) * 100) }}%
              <span v-if="view.completed">(completed)</span>
            </span>
          </div>
        </div>

        <p v-if="sop.description" class="text-sm text-gray-700 whitespace-pre-line">
          {{ sop.description }}
        </p>
      </section>

      <!-- Media viewer -->
      <section class="bg-white rounded-xl shadow-sm border p-4 space-y-3">
        <h2 class="text-sm font-semibold text-gray-800">
          Training media
        </h2>

        <div v-if="!mediaUrl" class="text-sm text-gray-500">
          No media file is attached to this SOP yet.
        </div>

        <div v-else class="space-y-3">
          <!-- Basic heuristic: video vs pdf vs generic link -->
          <div v-if="isVideo" class="rounded overflow-hidden bg-black/5">
            <video
              :src="mediaUrl"
              controls
              class="w-full max-h-[480px] bg-black"
            >
              Your browser does not support the video tag.
            </video>
          </div>

          <div
            v-else-if="isPdf"
            class="border rounded overflow-hidden"
          >
            <iframe
              :src="mediaUrl"
              class="w-full h-[480px]"
            >
              This browser cannot display embedded PDFs.
            </iframe>
          </div>

          <div v-else class="text-sm text-gray-700 space-y-2">
            <p>
              This SOP has associated media. Click below to open it in a new tab.
            </p>
            <a
              :href="mediaUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center px-3 py-1.5 rounded bg-emerald-600 text-white hover:bg-emerald-700"
            >
              Open training media
            </a>
          </div>

          <p class="text-xs text-gray-500">
            Once you’ve finished watching or reading the SOP, click
            <b>“Mark as viewed”</b> above to record completion and unlock related quizzes.
          </p>
        </div>
      </section>

      <!-- Debug: current view record -->
      <section v-if="view" class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          SOP view record (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(view, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
