<!-- frontend/pages/modules/[id].vue -->
<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()
const auth = useAuth()

const moduleId = computed(() => route.params.id as string)

const loading = ref(true)
const error = ref<string | null>(null)
const starting = ref(false)
const moduleData = ref<any | null>(null)

// Load module details
onMounted(loadModule)

async function loadModule () {
  loading.value = true
  error.value = null
  try {
    const data: any = await get(`/modules/${moduleId.value}/`)
    moduleData.value = data
  } catch (e: any) {
    error.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load module')
  } finally {
    loading.value = false
  }
}

// Start training using the SAME endpoint/logic as demo.vue
async function startTraining () {
  // Require login (frontend) before we even call the API
  if (!auth.loggedIn) {
    router.push(`/login?next=${encodeURIComponent(route.fullPath)}`)
    return
  }

  starting.value = true
  error.value = null

  try {
    // This must be a POST and must go through useApi()
    const data: any = await post(`/modules/${moduleId.value}/start/`, {})

    // Accept either { attempt_id: "…" } or { id: "…" } or nested
    const attemptId =
      data?.attempt_id ||
      data?.id ||
      data?.attempt?.id

    if (!attemptId) {
      throw new Error('No attempt_id returned from /modules/:id/start/')
    }

    // Navigate to the per-attempt quiz page
    await router.push(`/modules/${moduleId.value}/attempt/${attemptId}`)
  } catch (e: any) {
    // If auth is missing/invalid, you'll see:
    // {"detail": "Authentication credentials were not provided."}
    error.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to start attempt')
  } finally {
    starting.value = false
  }
}

function difficultyLabel (n?: number | null) {
  if (n == null) return 'Not set'
  if (n <= 1) return 'Easy'
  if (n === 2) return 'Medium'
  return 'Hard'
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <div class="flex items-center justify-between gap-2">
      <div>
        <h1 class="text-2xl font-bold">
          {{ moduleData?.title || 'Module' }}
        </h1>
        <p class="text-sm text-gray-600">
          View details and start a training attempt for this module.
        </p>
      </div>

      <NuxtLink
        to="/me/attempts"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
      >
        My attempts
      </NuxtLink>
    </div>

    <div v-if="loading" class="p-4 bg-gray-100 rounded text-sm">
      Loading module…
    </div>

    <div
      v-else-if="error"
      class="p-3 bg-red-100 rounded text-sm text-red-700 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="moduleData" class="space-y-4">
      <!-- Basic module info -->
      <section class="bg-white rounded-xl shadow p-4 space-y-2">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="text-xs text-gray-500 uppercase tracking-wide">
              Module
            </div>
            <div class="font-semibold">
              {{ moduleData.title }}
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-3 text-xs text-gray-600">
            <div>
              <span class="font-semibold">Difficulty:</span>
              <span>{{ difficultyLabel(moduleData.difficulty) }}</span>
            </div>
            <div>
              <span class="font-semibold">Pass mark:</span>
              <span>{{ moduleData.pass_mark ?? '—' }}%</span>
            </div>
          </div>

          <button
            type="button"
            class="px-4 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
            :disabled="starting"
            @click="startTraining"
          >
            <span v-if="starting">Starting…</span>
            <span v-else>Start training</span>
          </button>
        </div>
      </section>

      <!-- Config / debug -->
      <section class="bg-white rounded-xl shadow p-4 space-y-1 text-xs text-gray-600">
        <div class="font-semibold text-gray-800">
          Question pool:
          <span class="font-normal">
            {{ moduleData.question_pool || 'All questions' }}
          </span>
        </div>
        <div>
          Shuffle questions:
          <b>{{ moduleData.shuffle_questions ? 'Yes' : 'No' }}</b>
        </div>
        <div>
          Shuffle choices:
          <b>{{ moduleData.shuffle_choices ? 'Yes' : 'No' }}</b>
        </div>
        <div>
          Negative marking:
          <b>{{ moduleData.negative_marking ? 'Yes' : 'No' }}</b>
        </div>
        <div>
          SOP must be viewed before quiz:
          <b>{{ moduleData.require_sop_view ? 'Yes' : 'No' }}</b>
        </div>
      </section>

      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw module payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(moduleData, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
