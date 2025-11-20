<!-- frontend/pages/modules/[id].vue -->
<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const moduleId = computed(() => route.params.id as string)

type Module = {
  id: string
  title?: string | null
  description?: string | null
  difficulty?: number | null
  pass_mark?: number | null
  passing_score?: number | null
  question_pool_count?: number | null
  shuffle_questions?: boolean
  shuffle_choices?: boolean
  negative_marking?: boolean
  require_viewed?: boolean
  sop?: string | null
  // plus whatever else your serializer returns
}

const mod = ref<Module | null>(null)
const loading = ref(true)
const err = ref<string | null>(null)
const startError = ref<string | null>(null)
const starting = ref(false)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get(`/modules/${moduleId.value}/`)
    mod.value = data
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load module')
  } finally {
    loading.value = false
  }
}

async function startTraining () {
  startError.value = null
  starting.value = true
  try {
    // EXACTLY the same endpoint pattern as used in demo.vue
    const data: any = await post(`/modules/${moduleId.value}/start/`, {})

    // Backend might return { attempt_id: "..." } or { id: "..." }
    const attemptId = data.attempt_id || data.id
    if (!attemptId) {
      console.error('No attempt_id returned from /modules/<id>/start/', data)
      startError.value = 'Server did not return an attempt id.'
      return
    }

    await router.push(`/modules/${moduleId.value}/attempt/${attemptId}`)
  } catch (e: any) {
    console.error('Failed to start attempt', e)
    // bubble up backend error message if present
    if (e?.data) {
      startError.value = typeof e.data === 'string' ? e.data : JSON.stringify(e.data)
    } else {
      startError.value = e?.message || 'Failed to start training'
    }
  } finally {
    starting.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-4">
    <header class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          {{ mod?.title || 'Module' }}
        </h1>
        <p class="text-sm text-gray-600">
          View details and start a training attempt for this module.
        </p>
      </div>

      <button
        type="button"
        class="px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 text-sm"
        :disabled="starting || loading"
        @click="startTraining"
      >
        <span v-if="starting">Starting…</span>
        <span v-else>Start training</span>
      </button>
    </header>

    <div v-if="loading" class="text-sm text-gray-500">
      Loading module…
    </div>

    <div v-else-if="err" class="p-3 rounded bg-red-100 text-sm text-red-800 break-all">
      {{ err }}
    </div>

    <div v-else-if="mod" class="space-y-4">
      <section class="bg-white border rounded-xl shadow-sm p-4 space-y-2">
        <h2 class="text-sm font-semibold text-gray-800">
          {{ mod.title }}
        </h2>
        <p class="text-sm text-gray-600 whitespace-pre-line">
          {{ mod.description || 'No description provided.' }}
        </p>

        <dl class="mt-2 grid gap-2 text-xs text-gray-600 sm:grid-cols-2">
          <div class="flex items-center justify-between">
            <dt class="font-medium">Difficulty</dt>
            <dd>{{ mod.difficulty ?? '—' }}</dd>
          </div>
          <div class="flex items-center justify-between">
            <dt class="font-medium">Pass mark</dt>
            <dd>{{ mod.pass_mark ?? mod.passing_score ?? '—' }}%</dd>
          </div>
          <div class="flex items-center justify-between">
            <dt class="font-medium">Question pool</dt>
            <dd>
              <span v-if="mod.question_pool_count">
                {{ mod.question_pool_count }} questions per attempt
              </span>
              <span v-else>
                All questions
              </span>
            </dd>
          </div>
          <div class="flex items-center justify-between">
            <dt class="font-medium">Options</dt>
            <dd class="text-right">
              <span v-if="mod.shuffle_questions">Shuffle questions; </span>
              <span v-if="mod.shuffle_choices">Shuffle choices; </span>
              <span v-if="mod.negative_marking">Negative marking; </span>
              <span v-if="mod.require_viewed">SOP must be viewed before quiz</span>
              <span v-if="!mod.shuffle_questions && !mod.shuffle_choices && !mod.negative_marking && !mod.require_viewed">
                Default behaviour
              </span>
            </dd>
          </div>
        </dl>
      </section>

      <section v-if="startError" class="p-3 rounded bg-red-100 text-sm text-red-800 break-all">
        {{ startError }}
      </section>

      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw module payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(mod, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
