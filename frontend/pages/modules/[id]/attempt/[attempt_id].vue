<!-- frontend/pages/modules/[id]/attempt/[attempt_id].vue -->
<script setup>
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const moduleId = computed(() => route.params.id)
const attemptId = computed(() => route.params.attempt_id)

const loading = ref(true)
const err = ref(null)
const attempt = ref(null)

// local answer state: { [questionId]: Set of choiceIds (stored as array) }
const answers = ref({})

// submission state
const submitting = ref(false)
const submitError = ref(null)
const submitResult = ref(null)

// debug toggle
const showRaw = ref(false)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  submitError.value = null
  submitResult.value = null

  try {
    const data = await get(`/attempts/${attemptId.value}/`)
    attempt.value = data || null

    // Pre-fill answers if backend provides them (e.g. on resumed attempt)
    const initial = (data && data.answers) || {}
    const normalised = {}
    for (const [qid, choiceList] of Object.entries(initial)) {
      if (Array.isArray(choiceList)) {
        normalised[qid] = [...new Set(choiceList.map(String))]
      }
    }
    answers.value = normalised
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load attempt')
  } finally {
    loading.value = false
  }
}

// ---- Helpers to interpret the attempt payload ----

// Extract questions from common shapes
const questions = computed(() => {
  const a = attempt.value
  if (!a) return []

  if (Array.isArray(a.questions)) return a.questions
  if (Array.isArray(a.items)) return a.items
  if (a.quiz && Array.isArray(a.quiz.questions)) return a.quiz.questions

  return []
})

// Human-friendly title
const moduleTitle = computed(() => {
  const a = attempt.value
  if (!a) return `Module ${moduleId.value}`
  return a.module_title || a.module_name || a.module?.title || a.module?.name || `Module ${moduleId.value}`
})

function questionText (q) {
  return q.text || q.question || q.prompt || 'Untitled question'
}

function isMulti (q) {
  const t = String(q.qtype || q.type || '').toLowerCase()
  if (q.multi === true || q.multiple === true || q.allow_multiple === true) return true
  if (t.includes('multi') && !t.includes('single')) return true
  return false
}

function questionPoints (q) {
  const n = q.points ?? q.score ?? null
  if (!n && n !== 0) return null
  return Number.isNaN(Number(n)) ? null : Number(n)
}

// Choices: support several shapes
function questionChoices (q) {
  const raw =
    q.choices ||
    q.options ||
    q.answers ||
    []

  if (!Array.isArray(raw)) return []

  return raw.map((c, idx) => {
    if (c && typeof c === 'object') {
      return {
        id: c.id ?? c.pk ?? String(idx),
        text: c.text ?? c.label ?? c.answer ?? `Option ${idx + 1}`,
      }
    }
    // plain string
    return {
      id: String(idx),
      text: String(c),
    }
  })
}

// ---- Answer selection logic ----

function isSelected (questionId, choiceId) {
  const key = String(questionId)
  const cid = String(choiceId)
  const list = answers.value[key] || []
  return list.includes(cid)
}

function toggleChoice (question, choice) {
  const qid = question.id ?? question.qid ?? question.pk
  const cid = choice.id

  if (!qid || cid == null) return

  const key = String(qid)
  const current = answers.value[key] ? [...answers.value[key]] : []
  const multi = isMulti(question)

  if (multi) {
    // multi-select behaves like checkboxes
    if (current.includes(String(cid))) {
      answers.value[key] = current.filter(x => x !== String(cid))
    } else {
      current.push(String(cid))
      answers.value[key] = current
    }
  } else {
    // single-select behaves like radio
    answers.value[key] = [String(cid)]
  }
}

// ---- Submit answers ----

async function submitAnswers () {
  if (!questions.value.length) return

  submitting.value = true
  submitError.value = null
  submitResult.value = null

  try {
    // Build payload expected by backend: { question_id: [choice_id, ...] }
    const payloadAnswers = {}

    for (const q of questions.value) {
      const qid = q.id ?? q.qid ?? q.pk
      if (!qid) continue
      const key = String(qid)
      const selected = answers.value[key] || []
      // Only send if there is at least one selection; adjust if you want to send empties
      payloadAnswers[qid] = selected
    }

    const payload = { answers: payloadAnswers }

    const data = await post(`/attempts/${attemptId.value}/submit/`, payload)
    submitResult.value = data || { ok: true }
  } catch (e) {
    submitError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to submit answers')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          Training Attempt
        </h1>
        <p class="text-xs text-gray-500">
          Module: <span class="font-semibold">{{ moduleTitle }}</span><br>
          Module ID: {{ moduleId }} · Attempt ID: {{ attemptId }}
        </p>
      </div>

      <div class="flex flex-col items-end gap-2">
        <button
          type="button"
          class="px-4 py-2 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
          :disabled="submitting || loading || !questions.length"
          @click="submitAnswers"
        >
          <span v-if="submitting">Submitting…</span>
          <span v-else>Submit answers</span>
        </button>

        <NuxtLink
          :to="`/modules/${moduleId}`"
          class="text-xs text-gray-600 hover:underline"
        >
          ← Back to module
        </NuxtLink>
      </div>
    </div>

    <!-- Loading / error states -->
    <div v-if="loading" class="text-gray-500">
      Loading attempt…
    </div>

    <div v-else-if="err" class="text-red-600 break-all text-xs">
      {{ err }}
    </div>

    <div v-else-if="!attempt" class="text-sm text-gray-600">
      No attempt data returned.
    </div>

    <!-- Main quiz UI -->
    <div v-else class="space-y-6">
      <!-- Submission result banner -->
      <div v-if="submitResult" class="rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
        <div class="font-semibold mb-1">
          Answers submitted.
        </div>
        <div class="space-y-0.5">
          <div v-if="submitResult.score_percent !== undefined">
            Score: <span class="font-semibold">{{ submitResult.score_percent }}%</span>
          </div>
          <div v-if="submitResult.passed !== undefined">
            Status:
            <span
              class="font-semibold"
              :class="submitResult.passed ? 'text-emerald-800' : 'text-red-700'"
            >
              {{ submitResult.passed ? 'Passed' : 'Not passed' }}
            </span>
          </div>
          <div v-if="submitResult.message">
            {{ submitResult.message }}
          </div>
        </div>
      </div>

      <div v-if="submitError" class="rounded border border-red-200 bg-red-50 p-3 text-xs text-red-800">
        {{ submitError }}
      </div>

      <!-- Questions list -->
      <div v-if="questions.length === 0" class="text-sm text-gray-600">
        This attempt does not have any questions attached yet.
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="(q, idx) in questions"
          :key="q.id || idx"
          class="border rounded bg-white p-3 space-y-2"
        >
          <div class="flex justify-between gap-2">
            <div class="font-medium text-sm">
              Q{{ idx + 1 }}. {{ questionText(q) }}
            </div>
            <div class="flex items-center gap-2 text-[11px] text-gray-500">
              <span v-if="isMulti(q)" class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5">
                Multi-select
              </span>
              <span v-else class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5">
                Single-select
              </span>
              <span
                v-if="questionPoints(q) !== null"
                class="inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5"
              >
                {{ questionPoints(q) }} pts
              </span>
            </div>
          </div>

          <!-- Choices -->
          <div class="space-y-1">
            <button
              v-for="c in questionChoices(q)"
              :key="c.id"
              type="button"
              class="w-full flex items-center justify-between gap-2 px-2 py-1.5 rounded border text-xs text-left"
              :class="isSelected(q.id ?? q.qid ?? q.pk, c.id)
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-gray-200 hover:bg-gray-50'"
              @click="toggleChoice(q, c)"
            >
              <span class="flex-1">
                {{ c.text }}
              </span>
              <span
                class="inline-flex items-center justify-center w-4 h-4 rounded-full border text-[10px]"
                :class="isSelected(q.id ?? q.qid ?? q.pk, c.id)
                  ? 'border-emerald-600 bg-emerald-600 text-white'
                  : 'border-gray-300 bg-white text-transparent'"
              >
                ✓
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- Debug: raw JSON -->
      <div class="mt-4 border-t pt-3">
        <button
          type="button"
          class="text-xs text-gray-500 hover:text-gray-700 underline"
          @click="showRaw = !showRaw"
        >
          {{ showRaw ? 'Hide' : 'Show' }} raw attempt JSON (debug)
        </button>

        <pre
          v-if="showRaw"
          class="mt-2 text-[11px] bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-80"
        >{{ JSON.stringify(attempt, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>
