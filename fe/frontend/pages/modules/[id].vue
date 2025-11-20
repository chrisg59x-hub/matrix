<!-- frontend/pages/modules/[id].vue -->
<script setup>
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()
const auth = useAuth()

const moduleId = computed(() => route.params.id)

const loading = ref(true)
const err = ref(null)
const item = ref(null)

const starting = ref(false)
const startError = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data = await get(`/modules/${moduleId.value}/`)
    item.value = data
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load module')
  } finally {
    loading.value = false
  }
}

async function requireLogin () {
  // same pattern as demo.vue
  if (auth.loggedIn) return
  await router.push({
    path: '/login',
    query: { next: `/modules/${moduleId.value}` },
  })
  throw new Error('Not logged in')
}

async function startTraining () {
  try {
    await requireLogin()
  } catch {
    // user was redirected to login
    return
  }

  starting.value = true
  startError.value = null

  try {
    // 🔑 use the *same* endpoint as demo.vue
    const data = await post(`/modules/${moduleId.value}/attempt/start/`, {})

    // backend returns { attempt_id, module_id, questions: [...] }
    const attemptId = data?.attempt_id || data?.id
    if (!attemptId) {
      throw new Error('Backend did not return attempt_id')
    }

    await router.push(`/modules/${moduleId.value}/attempt/${attemptId}`)
  } catch (e) {
    console.error('Failed to start training', e)
    startError.value = e?.data
      ? JSON.stringify(e.data, null, 2)
      : (e?.message || 'Failed to start training')
  } finally {
    starting.value = false
  }
}

function difficultyLabel (n) {
  if (n == null) return 'Not set'
  if (n <= 1) return 'Beginner'
  if (n === 2) return 'Intermediate'
  if (n >= 3) return 'Advanced'
  return String(n)
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        {{ item?.title || 'Module' }}
      </h1>
      <p class="text-sm text-gray-600">
        View details and start a training attempt for this module.
      </p>
    </header>

    <!-- Loading / error -->
    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading module…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <!-- Content -->
    <div v-else-if="item" class="space-y-6">
      <!-- Main meta + start button -->
      <section class="bg-white rounded-xl shadow-sm border p-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div class="space-y-1">
          <div class="text-xs uppercase tracking-wide text-gray-500">
            Module
          </div>
          <div class="text-lg font-semibold">
            {{ item.title }}
          </div>
          <div class="text-xs text-gray-500">
            Difficulty:
            <b>{{ difficultyLabel(item.difficulty) }}</b>
            <span v-if="item.pass_mark != null">
              • Pass mark: <b>{{ item.pass_mark }}%</b>
            </span>
          </div>

          <div v-if="item.description" class="mt-2 text-sm text-gray-700 whitespace-pre-line">
            {{ item.description }}
          </div>

          <div class="mt-2 text-xs text-gray-500 space-y-1">
            <div v-if="item.question_pool_count">
              Question pool: up to
              <b>{{ item.question_pool_count }}</b>
              questions
            </div>
            <div v-else>
              Question pool: <b>All questions</b>
            </div>

            <div class="flex flex-wrap gap-1">
              <span
                v-if="item.shuffle_questions"
                class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-700"
              >
                Shuffle questions
              </span>
              <span
                v-if="item.shuffle_choices"
                class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-700"
              >
                Shuffle choices
              </span>
              <span
                v-if="item.negative_marking"
                class="inline-flex items-center rounded-full bg-red-50 px-2 py-0.5 text-[11px] text-red-700"
              >
                Negative marking
              </span>
              <span
                v-if="item.require_viewed"
                class="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-[11px] text-amber-700"
              >
                SOP must be viewed before quiz
              </span>
            </div>
          </div>
        </div>

        <div class="flex flex-col items-stretch gap-2 min-w-[180px]">
          <button
            type="button"
            class="inline-flex items-center justify-center px-4 py-2 rounded bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
            :disabled="starting"
            @click="startTraining"
          >
            <span v-if="starting">Starting…</span>
            <span v-else>Start training</span>
          </button>

          <NuxtLink
            to="/me/attempts"
            class="inline-flex items-center justify-center px-3 py-1.5 rounded border text-xs text-gray-700 hover:bg-gray-50"
          >
            My attempts
          </NuxtLink>

          <div
            v-if="startError"
            class="mt-1 text-[11px] text-red-600 whitespace-pre-wrap"
          >
            {{ startError }}
          </div>
        </div>
      </section>

      <!-- Optional: raw debug -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw module payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(item, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
