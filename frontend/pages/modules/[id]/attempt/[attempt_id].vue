<!-- frontend/pages/modules/[id]/attempt/[attempt_id].vue -->
<script setup>
const route = useRoute()
const { get } = useApi()

const moduleId = computed(() => route.params.id)
const attemptId = computed(() => route.params.attempt_id)

const loading = ref(true)
const err = ref(null)
const attempt = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data = await get(`/attempts/${attemptId.value}/`)
    attempt.value = data
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load attempt')
  } finally {
    loading.value = false
  }
}

/**
 * Try to locate questions in whatever shape the backend sends.
 * This will "just start working" once you add question payloads
 * (e.g. attempt.questions, attempt.payload.questions, etc.).
 */
const questions = computed(() => {
  const a = attempt.value
  if (!a) return []

  // Common shapes we might introduce later:
  if (Array.isArray(a.questions)) return a.questions
  if (a.payload && Array.isArray(a.payload.questions)) return a.payload.questions
  if (Array.isArray(a.items)) return a.items
  if (Array.isArray(a.question_set)) return a.question_set

  return []
})

function questionText (q) {
  return q.text || q.question || q.prompt || 'Question'
}

function optionsFor (q) {
  // Try a few likely shapes and then fall back
  if (Array.isArray(q.choices)) return q.choices
  if (Array.isArray(q.options)) return q.options
  if (Array.isArray(q.answers)) return q.answers
  return []
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          Training Attempt
        </h1>
        <p class="text-xs text-gray-500">
          Module ID: {{ moduleId }} · Attempt ID: {{ attemptId }}
        </p>
      </div>

      <NuxtLink
        :to="`/modules/${moduleId}`"
        class="text-xs text-gray-600 hover:underline"
      >
        ← Back to module
      </NuxtLink>
    </div>

    <div v-if="loading" class="text-gray-500">
      Loading attempt…
    </div>

    <div v-else-if="err" class="text-red-600 break-all text-xs">
      {{ err }}
      <p class="mt-2 text-gray-500">
        The attempt endpoint is reachable, but the quiz data may not be wired yet.
      </p>
    </div>

    <div v-else-if="!attempt" class="text-sm text-gray-600">
      No attempt data returned.
    </div>

    <div v-else class="space-y-6">
      <!-- 🔹 CASE 1: No questions yet – training-only module -->
      <div v-if="questions.length === 0" class="space-y-2">
        <p class="text-sm text-gray-700">
          This training attempt does not have any interactive quiz questions yet.
        </p>
        <p class="text-xs text-gray-500">
          You can still use the module content and SOPs for training. When you later
          add question data to the <code>/attempts/{{ attemptId }}/</code> response,
          this page will automatically start showing a quiz UI.
        </p>
      </div>

      <!-- 🔹 CASE 2: We have questions – basic quiz layout -->
      <div v-else class="space-y-4">
        <h2 class="text-sm font-semibold text-gray-800">
          Quiz questions (preview UI)
        </h2>

        <div class="space-y-3">
          <div
            v-for="(q, idx) in questions"
            :key="q.id || idx"
            class="border rounded p-3 bg-white"
          >
            <div class="font-medium text-sm mb-2">
              Q{{ idx + 1 }}. {{ questionText(q) }}
            </div>

            <div v-if="optionsFor(q).length" class="space-y-1">
              <label
                v-for="(opt, oIdx) in optionsFor(q)"
                :key="opt.id || oIdx"
                class="flex items-center gap-2 text-xs cursor-pointer"
              >
                <input
                  type="radio"
                  :name="`q-${idx}`"
                  class="rounded border-gray-300"
                >
                <span>
                  {{ opt.text || opt.label || opt }}
                </span>
              </label>
            </div>

            <div v-else class="text-xs text-gray-500">
              No options found for this question yet.
            </div>
          </div>
        </div>

        <p class="text-xs text-gray-500">
          This is a basic placeholder UI. Once we know the exact data shape
          (e.g. how answers are marked, scoring, etc.), we can wire in state,
          validation, and a “Submit attempt” POST call.
        </p>
      </div>

      <!-- 🔹 Always keep raw payload visible for debugging -->
      <section class="space-y-2">
        <h2 class="text-sm font-semibold text-gray-800">
          Raw attempt payload (debug)
        </h2>
        <pre class="text-xs bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto">
{{ JSON.stringify(attempt, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
