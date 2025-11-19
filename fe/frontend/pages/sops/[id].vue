<!-- frontend/pages/sops/[id].vue -->
<template>
  <div class="p-4 space-y-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">
          {{ sop?.title || 'Loading SOP…' }}
        </h1>
        <p v-if="sop" class="text-sm text-slate-500">
          Code: <span class="font-mono">{{ sop.code }}</span>
          · v{{ sop.version_major }}.{{ sop.version_minor }}
        </p>
        <p v-if="sop" class="text-xs text-slate-400">
          Status: {{ sop.status }} · Media: {{ sop.media_type }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          v-if="!completed"
          class="inline-flex items-center rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-60"
          :disabled="!sop"
          @click="markCompleted"
        >
          ✓ Mark as completed
        </button>
        <span
          v-else
          class="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700"
        >
          ✓ Completed
        </span>
      </div>
    </div>

    <!-- Error banner -->
    <div
      v-if="error"
      class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
    >
      {{ error }}
    </div>

    <!-- Media viewer -->
    <div
      v-if="sop"
      class="overflow-hidden rounded-xl border border-slate-200 bg-slate-50"
    >
      <!-- Video -->
      <template v-if="sop.media_type === 'video' && sop.media_file">
        <video
          ref="videoEl"
          controls
          class="block h-[70vh] w-full bg-black"
          @play="onVideoPlay"
          @pause="onVideoPause"
        >
          <source :src="sop.media_file" />
          Your browser does not support the video tag.
        </video>
      </template>

      <!-- PDF / PPTX -->
      <template
        v-else-if="(sop.media_type === 'pdf' || sop.media_type === 'pptx') && sop.media_file"
      >
        <iframe
          :src="sop.media_file"
          class="h-[75vh] w-full bg-white"
        />
      </template>

      <!-- External link -->
      <template v-else-if="sop.media_type === 'link' && sop.external_url">
        <div class="p-4">
          <p class="mb-2 text-sm text-slate-700">
            This SOP links to an external resource:
          </p>
          <a
            :href="sop.external_url"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-1 text-sm font-medium text-emerald-700 underline hover:text-emerald-800"
          >
            Open SOP in new tab
            <span aria-hidden="true">↗</span>
          </a>
        </div>
      </template>

      <!-- No media -->
      <template v-else>
        <div class="p-4 text-sm text-slate-600">
          No media attached for this SOP yet.
        </div>
      </template>
    </div>

    <!-- Tracking footer -->
    <div
      v-if="view"
      class="text-xs text-slate-400"
    >
      Tracked:
      {{ view.seconds_viewed || 0 }}s ·
      pages: {{ view.pages_viewed || 0 }} ·
      progress: {{ Math.round((view.progress || 0) * 100) }}%
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from '#imports'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const api = useApi()

const sop = ref<any | null>(null)
const view = ref<any | null>(null)
const error = ref<string | null>(null)
const completed = ref(false)

const videoEl = ref<HTMLVideoElement | null>(null)
const lastHeartbeatAt = ref<number | null>(null)
const lastVideoTime = ref(0)
let heartbeatTimer: any = null

const sopId = computed(() => route.params.id as string)

/**
 * Load SOP details from /api/sops/:id/
 */
async function loadSop() {
  try {
    error.value = null
    sop.value = await api.get(`/sops/${sopId.value}/`)
  } catch (e: any) {
    error.value = e?.message || 'Failed to load SOP'
  }
}

/**
 * Send heartbeat to /api/sops/:id/view/
 * - optionally marks completed
 * - includes seconds delta if we can infer from video time
 */
async function sendHeartbeat(options: { completedFlag?: boolean } = {}) {
  if (!sop.value) return

  const { completedFlag = false } = options

  try {
    const now = Date.now()
    let secondsDelta = 0

    if (videoEl.value) {
      const current = Math.floor(videoEl.value.currentTime || 0)
      secondsDelta = Math.max(0, current - lastVideoTime.value)
      lastVideoTime.value = current
    } else if (lastHeartbeatAt.value) {
      secondsDelta = Math.round((now - lastHeartbeatAt.value) / 1000)
    }
    lastHeartbeatAt.value = now

    const body: any = {}
    if (secondsDelta > 0) body.seconds_viewed = secondsDelta
    if (completedFlag) body.completed = true

    if (videoEl.value && sop.value?.duration_seconds) {
      const progress =
        (videoEl.value.currentTime || 0) / sop.value.duration_seconds
      body.progress = Math.max(0, Math.min(1, progress))
    }

    if (Object.keys(body).length === 0) return

    view.value = await api.post(`/sops/${sopId.value}/view/`, body)
    if (view.value?.completed) {
      completed.value = true
    }
  } catch {
    // best-effort; don’t block the UI if tracking fails
  }
}

function startHeartbeat() {
  stopHeartbeat()
  lastHeartbeatAt.value = Date.now()
  heartbeatTimer = setInterval(() => {
    void sendHeartbeat()
  }, 15000) // every 15s
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

async function markCompleted() {
  await sendHeartbeat({ completedFlag: true })
}

function onVideoPlay() {
  startHeartbeat()
}

function onVideoPause() {
  void sendHeartbeat()
}

onMounted(async () => {
  await loadSop()
  startHeartbeat()
})

onBeforeUnmount(() => {
  stopHeartbeat()
  void sendHeartbeat()
})
</script>
