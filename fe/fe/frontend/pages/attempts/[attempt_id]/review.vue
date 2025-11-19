<script setup lang="ts">
const route = useRoute()
const { get } = useApi()

type ChoiceReview = {
  id: string
  text: string
  is_correct: boolean
  selected: boolean
}

type QuestionReview = {
  id: string
  text: string
  qtype: string
  points: number
  explanation: string
  choices: ChoiceReview[]
}

type AttemptReview = {
  attempt_id: string
  module_id: string
  module_title: string
  score_percent: number
  passed: boolean
  created_at: string
  completed_at: string | null
  questions: QuestionReview[]
}

const loading = ref(true)
const err = ref<string | null>(null)
const data = ref<AttemptReview | null>(null)

onMounted(load)

async function load () {
  const attemptId = route.params.attempt_id as string
  if (!attemptId) {
    err.value = 'Missing attempt ID in route.'
    loading.value = false
    return
  }

  loading.value = true
  err.value = null
  try {
    const resp: any = await get(`/attempts/${attemptId}/review/`)
    data.value = resp
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load attempt review')
  } finally {
    loading.value = false
  }
}

function formatDateTime (value: string | null) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-5">
    <header v-if="data" class="space-y-1">
      <h1 class="text-2xl font-bold">
        Review attempt
      </h1>
      <p class="text-sm text-gray-600">
        Module:
        <span class="font-semibold">
          {{ data.module_title }}
        </span>
      </p>
      <div class="flex flex-wrap gap-3 text-sm text-gray-700 mt-1">
        <div>
          Score:
          <span class="font-semibold">
            {{ data.score_percent }}%
          </span>
        </div>
        <div>
          Result:
          <span
            class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
            :class="data.passed
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-red-50 text-red-700 border border-red-200'"
          >
            {{ data.passed ? 'Passed' : 'Failed' }}
          </span>
        </div>
        <div>
          Started:
          <span class="font-mono">
            {{ formatDateTime(data.created_at) }}
          </span>
        </div>
        <div>
          Completed:
          <span class="font-mono">
            {{ formatDateTime(data.completed_at) }}
          </span>
        </div>
      </div>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading attempt review…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else-if="data" class="space-y-4">
      <section class="space-y-3">
        <h2 class="text-sm font-semibold text-gray-800">
          Questions
        </h2>

        <div
          v-for="(q, idx) in data.questions"
          :key="q.id"
          class="bg-white border rounded-xl shadow-sm p-4 space-y-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <div class="text-xs text-gray-500 uppercase tracking-wide mb-0.5">
                Question {{ idx + 1 }}
              </div>
              <div class="font-medium text-gray-900 whitespace-pre-wrap">
                {{ q.text }}
              </div>
            </div>
            <div class="text-right text-xs text-gray-600">
              <div class="font-mono">
                {{ q.points }} pts
              </div>
            </div>
          </div>

<ul class="space-y-1">
  <li
    v-for="c in q.choices"
    :key="c.id"
    class="flex items-start gap-2 text-sm"
  >
    <span
      class="mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full border text-[10px]"
      :class="{
        'bg-emerald-600 border-emerald-600 text-white': c.selected && c.is_correct,
        'bg-red-600 border-red-600 text-white': c.selected && !c.is_correct,
        'bg-transparent border-gray-300 text-gray-400': !c.selected,
      }"
    >
      <span v-if="c.selected">&#10003;</span>
    </span>

    <div>
      <div class="text-gray-900">
        {{ c.text }}
      </div>
      <div class="text-[11px] text-gray-500 space-x-1">
        <span v-if="c.is_correct">
          ✅ correct answer
        </span>
        <span v-if="c.selected && !c.is_correct">
          ❌ you chose this
        </span>
        <span v-else-if="c.selected && c.is_correct">
          🎯 you chose this
        </span>
      </div>
    </div>
  </li>
</ul>

<!-- NEW: summary lines -->
<div class="mt-2 text-xs text-gray-700 space-y-0.5">
  <div>
    <span class="font-semibold">Your answer(s):</span>
    <span>
      {{
        q.choices.filter(c => c.selected).length
          ? q.choices.filter(c => c.selected).map(c => c.text).join(', ')
          : 'No answer given'
      }}
    </span>
  </div>
  <div>
    <span class="font-semibold">Correct answer(s):</span>
    <span>
      {{
        q.choices.filter(c => c.is_correct).length
          ? q.choices.filter(c => c.is_correct).map(c => c.text).join(', ')
          : 'No correct answer configured'
      }}
    </span>
  </div>
</div>


          <div
            v-if="q.explanation"
            class="mt-2 text-xs text-gray-600 bg-gray-50 border border-gray-100 rounded p-2 whitespace-pre-wrap"
          >
            {{ q.explanation }}
          </div>
        </div>
      </section>

      <!-- Optional debug -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw review payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(data, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
