<!-- frontend/pages/demo.vue -->
<script setup>
const { get, post } = useApi()
const { loading: attemptBusy, error: attemptError, fetchNext, submitQuestion, finishAttempt } = useAttempt()

const modules = ref([])
const modulesLoading = ref(true)
const modulesError = ref(null)

const activeModuleId = ref<string | null>(null)
const attemptId = ref<string | null>(null)

const currentQuestion = ref(null)
const remaining = ref(0)
const total = ref(0)
const selected = ref<string[]>([])

const finished = ref(false)
const result = ref(null)

const lastFeedback = ref(null)
const showFeedback = ref(false)
const submitting = ref(false)
const globalError = ref<string | null>(null)

const questionStartedAt = ref<number | null>(null)

onMounted(fetchModules)

async function fetchModules () {
  modulesLoading.value = true
  modulesError.value = null
  try {
    // lightweight list; you can tweak filters here if needed
    modules.value = await get('/modules/')
  } catch (e: any) {
    modulesError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load modules')
  } finally {
    modulesLoading.value = false
  }
}

async function startAttempt (moduleId: string) {
  globalError.value = null
  finished.value = false
  result.value = null
  lastFeedback.value = null
  showFeedback.value = false
  currentQuestion.value = null
  selected.value = []
  remaining.value = 0
  total.value = 0
  attemptId.value = null

  try {
    const res = await post(`/modules/${moduleId}/start/`, {})
    activeModuleId.value = moduleId
    attemptId.value = String(res.id ?? res.attempt_id ?? res.attemptId ?? res.id)
    await loadNextQuestion()
  } catch (e: any) {
    globalError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to start attempt')
  }
}

async function loadNextQuestion () {
  if (!attemptId.value) return
  globalError.value = null
  try {
    const data = await fetchNext(attemptId.value)
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
  } catch (e: any) {
    globalError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load next question')
  }
}

function isSingle (q: any) {
  if (!q) return false
  return q.qtype === 'single' || q.qtype === 'truefalse'
}

function toggleChoice (choiceId: string) {
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
  if (!attemptId.value || !currentQuestion.value) return
  if (!selected.value.length) {
    globalError.value = 'Please select at least one option.'
    return
  }
  submitting.value = true
  globalError.value = null
  try {
    let timeTaken: number | null = null
    if (typeof performance !== 'undefined' && questionStartedAt.value) {
      timeTaken = (performance.now() - questionStartedAt.value) / 1000
    }

    const res = await submitQuestion(
      attemptId.value,
      currentQuestion.value.id,
      selected.value,
      timeTaken ?? undefined
    )

    remaining.value = res.remaining ?? remaining.value

    if (res.correct !== undefined) {
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
  } catch (e: any) {
    globalError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to submit answer')
  } finally {
    submitting.value = false
  }
}

async function finalizeAttempt () {
  if (!attemptId.value) return
  finished.value = true
  try {
    result.value = await finishAttempt(attemptId.value)
  } catch (e: any) {
    globalError.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to finalise attempt')
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Demo: Quiz Engine
      </h1>
      <p class="text-sm text-gray-600">
        Pick a module, start an attempt, and answer questions one-by-one using the new engine.
      </p>
    </header>

    <!-- Module picker -->
    <section class="space-y-2">
      <h2 class="text-sm font-semibold text-gray-800">
        1. Choose a module
      </h2>

      <div v-if="modulesLoading" class="p-3 rounded bg-gray-100 text-xs">
        Loading modules…
      </div>
      <div v-else-if="modulesError" class="p-3 rounded bg-red-100 text-xs text-red-800 whitespace-pre-wrap">
        {{ modulesError }}
      </div>
      <div v-else-if="!modules.length" class="p-3 rounded bg-yellow-50 text-xs text-yellow-800">
        No modules found. Run the seed command to create demo data.
      </div>
      <div v-else class="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        <button
          v-for="m in modules"
          :key="m.id"
          type="button"
          class="p-3 rounded border text-left text-xs hover:border-emerald-500 hover:bg-emerald-50"
          @click="startAttempt(m.id)"
        >
          <div class="font-semibold text-gray-900 truncate">
            {{ m.title }}
          </div>
          <div class="text-[11px] text-gray-500 truncate">
            Skill: {{ m.skill || '—' }}
          </div>
        </button>
      </div>
    </section>

    <!-- Attempt panel -->
    <section class="space-y-3">
      <h2 class="text-sm font-semibold text-gray-800">
        2. Attempt
      </h2>

      <div v-if="globalError" class="p-3 rounded bg-red-100 text-xs text-red-800 whitespace-pre-wrap">
        {{ globalError }}
      </div>

      <div
        v-if="attemptId && !finished && currentQuestion"
        class="bg-white rounded-xl shadow p-4 space-y-4"
      >
        <div class="flex items-center justify-between text-[11px] text-gray-500">
          <div>
            Attempt:
            <code class="text-[10px] break-all">{{ attemptId }}</code>
          </div>
          <div>
            {{ total - remaining + 1 }} / {{ total || '…' }} questions
          </div>
        </div>

        <div class="text-sm font-medium text-gray-900">
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
          <div class="text-[11px] text-gray-500">
            Remaining: {{ remaining }} question{{ remaining === 1 ? '' : 's' }}
          </div>
          <button
            type="button"
            class="px-3 py-1.5 rounded bg-emerald-600 text-white text-xs hover:bg-emerald-700 disabled:opacity-60"
            :disabled="submitting || !selected.length"
            @click="submitCurrent"
          >
            <span v-if="submitting">Submitting…</span>
            <span v-else>Submit answer</span>
          </button>
        </div>
      </div>

      <div
        v-else-if="attemptId && !finished && !currentQuestion"
        class="p-3 rounded bg-gray-50 text-xs text-gray-700"
      >
        No questions currently loaded. Click a module above to start again.
      </div>

      <!-- Per-question feedback -->
      <div
        v-if="showFeedback && lastFeedback"
        class="bg-gray-50 border border-dashed rounded-xl p-4 space-y-1 text-xs"
      >
        <div class="font-semibold uppercase text-gray-600">
          Feedback
        </div>
        <div :class="lastFeedback.correct ? 'text-emerald-700' : 'text-red-700'">
          {{ lastFeedback.message || (lastFeedback.correct ? 'Correct' : 'Incorrect') }}
        </div>
        <div v-if="lastFeedback.earned != null" class="text-gray-600">
          Earned {{ lastFeedback.earned }} / {{ lastFeedback.max_points }} pts
        </div>
        <div v-if="!finished && remaining > 0" class="pt-1">
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
        class="bg-white rounded-xl shadow p-4 space-y-2 text-xs"
      >
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold text-gray-900">
              Final result
            </div>
            <div class="text-gray-700">
              Score: <b>{{ result.percent }}%</b> ·
              <span :class="result.passed ? 'text-emerald-700' : 'text-red-700'">
                {{ result.passed ? 'PASSED' : 'FAILED' }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="Array.isArray(result.feedback) && result.feedback.length" class="space-y-1 pt-2">
          <div class="font-semibold text-gray-800">
            Feedback by question
          </div>
          <div
            v-for="f in result.feedback"
            :key="f.question_id"
            class="border rounded p-2 space-y-1"
          >
            <div class="flex justify-between">
              <span>
                {{ f.correct ? '✅' : '❌' }}
              </span>
              <span>
                {{ f.earned }} / {{ f.max }} pts
              </span>
            </div>
            <div class="text-gray-700">
              {{ f.message }}
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Tiny debug -->
    <section class="space-y-1 text-[10px] text-gray-500">
      <div v-if="attemptBusy">
        Engine busy…
      </div>
      <div v-if="attemptError">
        Engine error: {{ attemptError }}
      </div>
    </section>
  </div>
</template>
