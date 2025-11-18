<script setup>
const route = useRoute()
const router = useRouter()
const { get } = useApi()
const { loading: attemptBusy, error: attemptError, fetchNext, submitQuestion, finishAttempt } = useAttempt()

const moduleId = computed(() => route.params.id)
const attemptId = computed(() => route.params.attempt_id)

const loading = ref(true)
const err = ref(null)
const attempt = ref(null)

const currentQuestion = ref(null)
const remaining = ref(0)
const total = ref(0)
const selected = ref([])

const submitting = ref(false)
const finished = ref(false)
const result = ref(null)

const lastFeedback = ref(null)
const showFeedback = ref(false)
const questionStartedAt = ref(null)

const answeredCount = computed(() =>
  total.value > 0 ? (total.value - remaining.value) : 0
)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    // basic attempt info (module title, timestamps, last score, etc.)
    attempt.value = await get(`/attempts/${attemptId.value}/`)
    await loadNextQuestion()
  } catch (e) {
    err.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load attempt')
  } finally {
    loading.value = false
  }
}

async function loadNextQuestion () {
  err.value = null
  try {
    const data = await fetchNext(String(attemptId.value))
    total.value = data.total || 0
    remaining.value = data.remaining || 0
    currentQuestion.value = data.question
    selected.value = []
    lastFeedback.value = null
    showFeedback.value = false

    if (typeof performance !== 'undefined') {
      questionStartedAt.value = performance.now()
    } else {
      questionStartedAt.value = null
    }

    if (!data.question) {
      await finalizeAttempt()
    }
  } catch (e) {
    err.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load next question')
  }
}

function isSingle (q) {
  if (!q) return false
  return q.qtype === 'single' || q.qtype === 'truefalse'
}

function toggleChoice (choiceId) {
  if (!currentQuestion.value) return
  if (isSingle(currentQuestion.value)) {
    selected.value = [choiceId]
  } else {
    const set = new Set(selected.value)
    if (set.has(choiceId)) set.delete(choiceId)
    else set.add(choiceId)
    selected.value = Array.from(set)
  }
}

async function submitCurrent () {
  if (!currentQuestion.value) return
  if (!selected.value.length) {
    err.value = 'Please select at least one option.'
    return
  }
  submitting.value = true
  err.value = null
  try {
    let timeTaken = null
    if (typeof performance !== 'undefined' && questionStartedAt.value) {
      timeTaken = (performance.now() - questionStartedAt.value) / 1000
    }

    const res = await submitQuestion(
      String(attemptId.value),
      currentQuestion.value.id,
      selected.value,
      timeTaken == null ? undefined : timeTaken
    )

    if (typeof res.remaining === 'number') {
      remaining.value = res.remaining
    }

    if (typeof res.correct !== 'undefined') {
      lastFeedback.value = res
      showFeedback.value = true

      if (res.completed || res.remaining === 0) {
        await finalizeAttempt()
      }
    } else {
      if (res.completed || res.remaining === 0) {
        await finalizeAttempt()
      } else {
        await loadNextQuestion()
      }
    }
  } catch (e) {
    err.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to submit answer')
  } finally {
    submitting.value = false
  }
}

async function finalizeAttempt () {
  finished.value = true
  try {
    result.value = await finishAttempt(String(attemptId.value))
  } catch (e) {
    err.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to finalise attempt')
  }
}

function goBack () {
  router.push('/me/attempts')
}

function questionLabel (idx) {
  return `Q${idx + 1}`
}
</script>

<template>
  <div class="space-y-4">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Module attempt
      </h1>
      <p class="text-sm text-gray-600">
        Module:
        <span class="font-medium">
          {{ attempt?.module_title || moduleId }}
        </span>
      </p>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading attempt…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else class="grid gap-4 lg:grid-cols-[2fr,1fr]">
      <!-- Left: question flow / result -->
      <section class="space-y-4">
        <div class="flex items-center justify-between text-xs text-gray-600">
          <div>
            Questions answered:
            <b>{{ answeredCount }}</b> / {{ total || '…' }}
          </div>
          <div v-if="attempt?.score != null">
            Last score: <b>{{ attempt.score }}%</b>
          </div>
        </div>

        <!-- Active question -->
        <div
          v-if="!finished && currentQuestion"
          class="bg-white rounded-xl shadow p-4 space-y-4"
        >
          <div class="text-xs uppercase tracking-wide text-gray-500">
            Question {{ answeredCount + 1 }} of {{ total || '…' }}
          </div>
          <div class="font-medium text-gray-900">
            {{ currentQuestion.text }}
          </div>

          <div class="space-y-2">
            <label
              v-for="opt in currentQuestion.choices"
              :key="opt.id"
              class="flex items-center gap-2 text-sm cursor-pointer"
            >
              <input
                :type="isSingle(currentQuestion) ? 'radio' : 'checkbox'"
                :name="`q-${currentQuestion.id}`"
                class="rounded border-gray-300"
                :value="opt.id"
                :checked="selected.includes(opt.id)"
                @change="toggleChoice(opt.id)"
              >
              <span>{{ opt.text }}</span>
            </label>
          </div>

          <div class="flex items-center justify-between pt-2">
            <div class="text-xs text-gray-500">
              {{ remaining }} question{{ remaining === 1 ? '' : 's' }} remaining
            </div>
            <button
              type="button"
              class="px-4 py-1.5 rounded bg-emerald-600 text-white text-xs hover:bg-emerald-700 disabled:opacity-60"
              :disabled="submitting || !selected.length"
              @click="submitCurrent"
            >
              <span v-if="submitting">Submitting…</span>
              <span v-else>Submit answer</span>
            </button>
          </div>
        </div>

        <!-- No questions -->
        <div
          v-else-if="!finished && !currentQuestion"
          class="bg-white rounded-xl shadow p-4"
        >
          <p class="text-sm text-gray-700">
            No questions available for this module.
          </p>
        </div>

        <!-- Per-question feedback -->
        <div
          v-if="showFeedback && lastFeedback"
          class="bg-gray-50 border border-dashed rounded-xl p-4 space-y-1"
        >
          <div class="text-xs font-semibold uppercase text-gray-600">
            Feedback
          </div>
          <div
            class="text-sm"
            :class="lastFeedback.correct ? 'text-emerald-700' : 'text-red-700'"
          >
            {{ lastFeedback.message || (lastFeedback.correct ? 'Correct' : 'Incorrect') }}
          </div>
          <div v-if="lastFeedback.earned != null" class="text-xs text-gray-600">
            Earned {{ lastFeedback.earned }} / {{ lastFeedback.max_points }} pts
          </div>
          <div class="pt-1" v-if="!finished && remaining > 0">
            <button
              type="button"
              class="px-3 py-1 text-xs rounded bg-gray-900 text-white hover:bg-black"
              @click="loadNextQuestion"
            >
              Next question
            </button>
          </div>
        </div>

        <!-- Final result -->
        <div
          v-if="finished && result"
          class="bg-white rounded-xl shadow p-4 space-y-3"
        >
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold">
                Attempt result
              </h2>
              <p class="text-xs text-gray-600">
                Score:
                <b>{{ result.percent }}%</b>
                · Passed:
                <b :class="result.passed ? 'text-emerald-700' : 'text-red-700'">
                  {{ result.passed ? 'Yes' : 'No' }}
                </b>
              </p>
            </div>
            <button
              type="button"
              class="px-3 py-1 text-xs rounded bg-gray-900 text-white hover:bg-black"
              @click="goBack"
            >
              Back to my attempts
            </button>
          </div>

          <div
            v-if="Array.isArray(result.feedback) && result.feedback.length"
            class="space-y-2"
          >
            <div class="text-xs font-semibold uppercase text-gray-600">
              Feedback by question
            </div>
            <div
              v-for="(f, idx) in result.feedback"
              :key="f.question_id || idx"
              class="border rounded-lg p-2 text-xs space-y-1"
            >
              <div class="flex justify-between">
                <span class="font-medium">
                  {{ questionLabel(idx) }}
                </span>
                <span>
                  {{ f.earned }} / {{ f.max }} pts ·
                  <span :class="f.correct ? 'text-emerald-700' : 'text-red-700'">
                    {{ f.correct ? 'Correct' : 'Incorrect' }}
                  </span>
                </span>
              </div>
              <div class="text-gray-700">
                {{ f.message }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Right: metadata + debug -->
      <aside class="space-y-3">
        <div class="bg-white rounded-xl shadow p-4 text-xs space-y-1">
          <div class="font-semibold text-gray-800">
            Attempt info
          </div>
          <div>
            ID:
            <code class="text-[10px] break-all">{{ attempt?.id }}</code>
          </div>
          <div>
            Module: {{ attempt?.module_title || moduleId }}
          </div>
          <div>Created: {{ attempt?.created_at }}</div>
          <div v-if="attempt?.completed_at">
            Completed: {{ attempt.completed_at }}
          </div>
          <div v-if="attempt?.score != null">
            Score: {{ attempt.score }}%
          </div>
          <div v-if="attempt?.passed != null">
            Passed:
            <span :class="attempt.passed ? 'text-emerald-700' : 'text-red-700'">
              {{ attempt.passed ? 'Yes' : 'No' }}
            </span>
          </div>
        </div>

        <section class="space-y-2">
          <h2 class="text-xs font-semibold text-gray-800">
            Raw attempt payload (debug)
          </h2>
          <pre class="text-[10px] bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(attempt, null, 2) }}
          </pre>
        </section>
      </aside>
    </div>
  </div>
</template>
