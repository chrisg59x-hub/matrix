<!-- frontend/pages/modules/[id]/attempt/[attempt_id].vue -->
<script setup lang="ts">
definePageMeta({
  ssr: false,
})
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()   // <- use GET + POST

const moduleId = computed(() => route.params.id as string)
const attemptId = computed(() => route.params.attempt_id as string)

type Choice = {
  id: string
  text: string
}

type Question = {
  id: string
  text: string
  qtype?: string | null
  points?: number | null
  choices: Choice[]
  explanation?: string | null
}

const loading = ref(true)
const submitting = ref(false)
const err = ref<string | null>(null)

const attempt = ref<any | null>(null) // currently unused, kept for future stats if you want
const currentQuestion = ref<Question | null>(null)
const selected = ref<string[]>([])

const totalQuestions = ref<number>(0)
const answeredCount = ref<number>(0)

const feedback = ref<any | null>(null)
const finished = ref(false)
const finishSummary = ref<any | null>(null)

onMounted(() => {
  // Load the first question as soon as we land on this page
  loadNextQuestion(true)
})

function resetStateForNewQuestion () {
  feedback.value = null
  selected.value = []
}

function isMultiSelect (q: Question | null) {
  if (!q) return false
  const t = (q.qtype || '').toLowerCase()
  return t === 'multi' || t === 'multiple' || t === 'multi-select'
}

function toggleChoice (choiceId: string) {
  const q = currentQuestion.value
  if (!q) return

  if (!isMultiSelect(q)) {
    // single / truefalse behaviour – radio style
    if (selected.value.length === 1 && selected.value[0] === choiceId) {
      selected.value = []
    } else {
      selected.value = [choiceId]
    }
  } else {
    // multi-select – checkbox style
    if (selected.value.includes(choiceId)) {
      selected.value = selected.value.filter(id => id !== choiceId)
    } else {
      selected.value = [...selected.value, choiceId]
    }
  }
}

async function loadFinishSummary () {
  // Called when the backend reports done = true
  try {
    const resp: any = await post(`/attempts/${attemptId.value}/finish/`, {})
    finishSummary.value = resp
  } catch (e: any) {
    console.error('Failed to load finish summary', e)
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load result')
  }
}

async function loadNextQuestion (initial = false) {
  loading.value = true
  err.value = null
  if (!initial) {
    resetStateForNewQuestion()
  }

  try {
    // BEFORE:
    // const resp: any = await post(`/attempts/${attemptId.value}/next/`, {})

    // AFTER: use GET to match the DRF view
    const resp: any = await get(`/attempts/${attemptId.value}/next/`)

    console.log('next/ response', resp)

    attempt.value = resp.attempt || attempt.value

    if (resp.done) {
      finished.value = true
      finishSummary.value = resp.summary || resp
      currentQuestion.value = null
      return
    }

    const q = resp.question as Question | undefined
    if (!q) {
      throw new Error('Backend did not return a question')
    }

    currentQuestion.value = q

    const progress = resp.progress || {}
    totalQuestions.value =
      progress.total ||
      progress.total_questions ||
      resp.total_questions ||
      0

    answeredCount.value =
      progress.answered ??
      progress.current_index ??
      (totalQuestions.value && resp.remaining_questions != null
        ? totalQuestions.value - resp.remaining_questions
        : 0)

    selected.value = Array.isArray(resp.preselected_choices)
      ? resp.preselected_choices
      : []
  } catch (e: any) {
    console.error('Failed to load next question', e)
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load next question')
  } finally {
    loading.value = false
  }
}

async function submitAnswer () {
  if (!currentQuestion.value) return
  if (!selected.value.length) {
    // you can relax this if you want to allow skipping
    err.value = 'Please select at least one answer.'
    return
  }

  submitting.value = true
  err.value = null

  try {
    const payload = {
      question_id: currentQuestion.value.id,
      choice_ids: selected.value,
    }

    // Backend submit_question returns:
    // { attempt_id, question_id, earned, max, correct, message }
    const resp: any = await post(`/attempts/${attemptId.value}/submit/`, payload)
    console.log('submit/ response', resp)

    feedback.value = resp

    // We deliberately DO NOT auto-advance here, so that
    // the user can see feedback then click "Next question".
  } catch (e: any) {
    console.error('Failed to submit answer', e)
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to submit answer')
  } finally {
    submitting.value = false
  }
}

async function goNextAfterFeedback () {
  await loadNextQuestion(false)
}

function goToReview () {
  router.push(`/attempts/${attemptId.value}/review`)
}

const progressLabel = computed(() => {
  if (!totalQuestions.value) return ''
  const currentIndex = Math.min(
    answeredCount.value + (currentQuestion.value ? 1 : 0),
    totalQuestions.value
  )
  return `Question ${currentIndex} of ${totalQuestions.value}`
})
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <header class="space-y-1">
      <div class="text-xs text-gray-500">
        <NuxtLink to="/modules" class="hover:underline">
          Modules
        </NuxtLink>
        <span class="mx-1">/</span>
        <NuxtLink :to="`/modules/${moduleId}`" class="hover:underline">
          Module
        </NuxtLink>
        <span class="mx-1">/</span>
        <span>Attempt</span>
      </div>
      <h1 class="text-xl font-bold">
        Module attempt
      </h1>
      <p class="text-xs text-gray-500">
        Answer one question at a time. Your progress is saved on each submit.
      </p>
    </header>

    <div v-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <!-- Finished view -->
    <div
      v-if="finished"
      class="bg-white border rounded-xl shadow p-4 space-y-3"
    >
      <h2 class="text-lg font-semibold">
        Attempt completed
      </h2>
      <div class="text-sm text-gray-700 space-y-1">
        <div v-if="finishSummary?.percent != null">
          <span class="font-semibold">Score:</span>
          <span> {{ finishSummary.percent }}%</span>
        </div>
        <div v-if="finishSummary?.passed != null">
          <span class="font-semibold">Result:</span>
          <span>
            {{ finishSummary.passed ? 'Passed' : 'Failed' }}
          </span>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700"
          @click="goToReview"
        >
          View detailed review
        </button>
        <NuxtLink
          to="/me/attempts"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        >
          Back to my attempts
        </NuxtLink>
      </div>

      <div
        v-if="finishSummary"
        class="mt-3 text-[11px] text-gray-500"
      >
        <div class="font-semibold mb-1">
          Raw summary (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-2 overflow-x-auto max-h-40">
{{ JSON.stringify(finishSummary, null, 2) }}
        </pre>
      </div>
    </div>

    <!-- Question runner -->
    <div
      v-else
      class="bg-white border rounded-xl shadow p-4 space-y-4"
    >
      <div class="flex items-center justify-between text-xs text-gray-500">
        <div>
          {{ progressLabel }}
        </div>
        <!-- attempt.score_percent is not returned by next/ currently,
             so this block will usually be hidden; left in case you add it later -->
        <div v-if="attempt?.score_percent != null">
          Current score: <b>{{ attempt.score_percent }}%</b>
        </div>
      </div>

      <div v-if="loading && !currentQuestion" class="text-sm text-gray-500">
        Loading question…
      </div>

      <div v-else-if="currentQuestion" class="space-y-3">
        <div class="space-y-1">
          <div class="text-sm font-medium">
            {{ currentQuestion.text }}
          </div>
          <div class="text-[11px] text-gray-500">
            Type: {{ (currentQuestion.qtype || 'single').toUpperCase() }}
            <span v-if="currentQuestion.points != null">
              · {{ currentQuestion.points }} pts
            </span>
          </div>
        </div>

        <div class="space-y-1">
          <button
            v-for="choice in currentQuestion.choices"
            :key="choice.id"
            type="button"
            class="w-full text-left px-3 py-2 border rounded text-sm flex items-center gap-2"
            :class="selected.includes(choice.id)
              ? 'bg-emerald-50 border-emerald-500'
              : 'bg-white hover:bg-gray-50 border-gray-200'"
            @click="toggleChoice(choice.id)"
          >
            <span
              class="inline-flex items-center justify-center w-4 h-4 border rounded-full text-[10px]"
              :class="selected.includes(choice.id)
                ? 'border-emerald-600 bg-emerald-600 text-white'
                : 'border-gray-300 text-transparent'"
            >
              ✓
            </span>
            <span>{{ choice.text }}</span>
          </button>
        </div>

        <!-- Submit / actions -->
        <div class="flex flex-wrap gap-2 pt-2">
          <button
            type="button"
            class="px-4 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
            :disabled="submitting || loading"
            @click="submitAnswer"
          >
            {{ submitting ? 'Submitting…' : 'Submit answer' }}
          </button>

          <button
            v-if="feedback && !finished"
            type="button"
            class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
            :disabled="loading"
            @click="goNextAfterFeedback"
          >
            Next question
          </button>
        </div>

        <!-- Feedback (immediate feedback from submit/ endpoint) -->
        <div
          v-if="feedback"
          class="mt-2 text-sm"
        >
          <div
            v-if="typeof feedback.correct === 'boolean'"
            class="mb-1"
          >
            <span
              v-if="feedback.correct"
              class="inline-flex items-center rounded-full bg-emerald-100 text-emerald-700 px-2 py-0.5 text-xs"
            >
              ✓ Correct
            </span>
            <span
              v-else
              class="inline-flex items-center rounded-full bg-red-100 text-red-700 px-2 py-0.5 text-xs"
            >
              ✕ Incorrect
            </span>
          </div>
          <div v-if="feedback.message" class="text-xs text-gray-700">
            {{ feedback.message }}
          </div>
        </div>
      </div>

      <div
        v-else
        class="text-sm text-gray-500"
      >
        No more questions available for this attempt.
      </div>
    </div>
  </div>
</template>
