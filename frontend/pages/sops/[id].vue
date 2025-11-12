<script setup lang="ts">
const route = useRoute()
const { post } = useApi()

const sopId = route.params.id as string
const mtype = (route.query.type as string) || 'video' // 'video' | 'pdf'
const src = (route.query.src as string) || ''

const progress = ref(0)
const pagesViewed = ref(0)
const completed = ref(false)
let interval:any = null

async function ping(extra: Partial<{completed:boolean}> = {}) {
  try {
    await post(`/sops/${sopId}/view/`, {
      seconds_viewed: 5,
      pages_viewed: pagesViewed.value || 0,
      progress: Math.max(0, Math.min(1, progress.value)),
      completed: extra.completed ?? completed.value
    })
  } catch {}
}
onMounted(() => { interval = setInterval(() => ping(), 5000) })
onBeforeUnmount(() => { clearInterval(interval) })

function onTimeUpdate(e: Event) {
  const el = e.target as HTMLVideoElement
  if (!el || !el.duration) return
  progress.value = el.currentTime / el.duration
}
async function onEnded() {
  completed.value = true
  progress.value = 1
  await ping({ completed: true })
}
</script>

<template>
  <div class="max-w-5xl mx-auto p-4 space-y-4">
    <h1 class="text-xl font-semibold">SOP Viewer</h1>

    <div v-if="mtype==='video'">
      <video :src="src" controls class="w-full rounded border"
             @timeupdate="onTimeUpdate" @ended="onEnded"/>
      <div class="text-sm text-gray-600 mt-2">Progress: {{ Math.round(progress*100) }}%</div>
    </div>

    <div v-else-if="mtype==='pdf'">
      <iframe :src="src" class="w-full h-[80vh] border rounded"></iframe>
      <div class="text-sm text-gray-600">(Basic PDF view — heartbeats track time/progress.)</div>
    </div>

    <div v-else class="text-red-600">Unknown media type. Provide ?type=video|pdf&src=&lt;URL&gt;.</div>
  </div>
</template>
