<script setup>
const route = useRoute()
const router = useRouter()
const { get } = useApi()

const attemptId = computed(() => route.params.id)

const loading = ref(true)
const error = ref(null)
const review = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  try {
    review.value = await get(`/attempts/${attemptId.value}/review/`)
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load attempt review')
  } finally {
    loading.value = false
  }
}

function goBack () {
  router.push('/me/attempts')
}

function choiceClasses (question, choice) {
  const selected = (question.selected_choice_ids || []).map(String)
  const isSelected = selected.includes(String(choice.id))

  if (choice.is_correct && isSelected) {
    return 'border-emerald-500 bg-emerald-50'
  }
  if (choice.is_correct && !isSelected) {
    return 'border-emerald-300 bg-emerald-25'
  }
  if (!choice.is_correct && isSelected) {
    return 'border-red-400 bg-red-50'
  }
  return 'border-gray-200 bg-white'
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Attempt review
        </h1>
        <p v-if="review" class="text-sm text-gray-600">
          Module:
          <span class="font-medium">
            {{ review.module_title }}
          </span>
        </p>
      </div>
      <button
        type="button"
        class="px-3 py-1.5 rounded bg-gray-900 text-white text-xs hover:bg-black"
        @click="goBack"
      >
        Back to my attempts
      </button>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading attempt review…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="review" class="space-y-4">
      <!-- Summary card -->
      <section class="bg-white rounded-xl shadow p-4 flex flex-wrap gap-4 text-sm">
        <div class="space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Score
          </div>
          <div class="text-2xl font-semibold">
            {{ review.score }}%
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Result
          </div>
          <div
            class="text-lg font-semibold"
            :class="review.passed ? 'text-emerald-700' : 'text-red-700'"
          >
            {{ review.passed ? 'Passed' : 'Failed' }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            User
          </div>
          <div>
            {{ review.username }}
          </div>
        </div>
        <div class="space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Timing
          </div>
          <div class="text-xs text-gray-700">
            Started: {{ review.created_at }}<br>
            Completed: {{ review.completed_at || '—' }}
          </div>
        </div>
      </section>

      <!-- Question-by-question breakdown -->
      <section class="space-y-3">
        <h2 class="text-sm font-semibold text-gray-800">
          Questions
        </h2>

        <div
          v-for="(q, idx) in review.questions"
          :key="q.id"
          class="bg-white rounded-xl shadow p-4 space-y-3 text-sm"
        >
          <div class="flex items-start justify-between gap-2">
            <div>
              <div class="text-xs text-gray-500 uppercase tracking-wide">
                Question {{ idx + 1 }} ({{ q.qtype }})
              </div>
              <div class="font-medium text-gray-900">
                {{ q.text }}
              </div>
            </div>
            <div class="text-right text-xs">
              <div>
                {{ q.earned }} / {{ q.max_points }} pts
              </div>
              <div
                :class="q.correct ? 'text-emerald-700' : 'text-red-700'"
              >
                {{ q.correct ? 'Correct' : 'Incorrect' }}
              </div>
            </div>
          </div>

          <div class="space-y-1">
            <div
              v-for="choice in q.choices"
              :key="choice.id"
              class="flex items-center gap-2 p-2 border rounded text-xs"
              :class="choiceClasses(q, choice)"
            >
              <span>
                <span v-if="choice.is_correct">✅</span>
                <span v-else-if="(q.selected_choice_ids || []).map(String).includes(String(choice.id))">✖</span>
              </span>
              <span>{{ choice.text }}</span>
            </div>
          </div>

          <div v-if="q.explanation" class="text-xs text-gray-600 pt-1">
            <span class="font-semibold">Explanation:</span>
            {{ q.explanation }}
          </div>
        </div>
      </section>

      <!-- Debug -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw review payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(review, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
