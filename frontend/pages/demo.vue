<script setup lang="ts">
const { user, token, login, logout, me } = useAuth()
const { get, post } = useApi()
const username = ref('employee')
const password = ref('employee123')
const step = ref<'login'|'dashboard'|'attempt'|'result'>('login')
const modules = ref<any[]>([])
const selectedModule = ref<any | null>(null)
const startPayload = ref<any | null>(null)
const answers = ref<Record<string, string[]>>({})
const result = ref<any | null>(null)
const busy = ref(false)
const err = ref<string | null>(null)

onMounted(async () => {
  if (token.value) {
    try { await me(); await loadModules(); step.value = 'dashboard' } catch {}
  }
})

async function doLogin() {
  err.value = null; busy.value = true
  try { await login(username.value, password.value); await loadModules(); step.value = 'dashboard' }
  catch (e:any) { err.value = e?.data?.detail || 'Login failed' }
  finally { busy.value = false }
}

async function loadModules() {
  const data:any = await get('/modules/')
  modules.value = Array.isArray(data) ? data : (data.results || [])
}

async function startAttempt(mod:any) {
  busy.value = true; err.value = null
  try {
    selectedModule.value = mod
    const sp = await post(`/modules/${mod.id}/start/`, {})
    startPayload.value = sp
    answers.value = {}
    for (const q of sp.questions) answers.value[q.id] = []
    step.value = 'attempt'
  } catch (e:any) { err.value = e?.data?.detail || 'Could not start attempt' }
  finally { busy.value = false }
}

function toggleChoice(qid:string, cid:string, qtype:string) {
  if (qtype === 'single' || qtype === 'truefalse') {
    answers.value[qid] = [cid]
  } else {
    const set = new Set(answers.value[qid] || [])
    set.has(cid) ? set.delete(cid) : set.add(cid)
    answers.value[qid] = [...set]
  }
}

async function submitAttempt() {
  if (!startPayload.value) return
  busy.value = true; err.value = null
  try {
    const payload = { answers: Object.entries(answers.value).map(([question_id, choice_ids]) => ({ question_id, choice_ids })) }
    result.value = await post(`/attempts/${startPayload.value.attempt_id}/submit/`, payload)
    step.value = 'result'
  } catch (e:any) { err.value = e?.data?.detail || 'Submit failed' }
  finally { busy.value = false }
}

function backToDashboard() {
  result.value = null; startPayload.value = null; selectedModule.value = null; step.value = 'dashboard'
}
</script>

<template>
  <div class="min-h-screen p-6 max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">Matrix Demo</h1>

    <div v-if="err" class="mb-4 p-3 border border-red-400 text-red-700 rounded">{{ err }}</div>

    <section v-if="step === 'login'" class="space-y-3 max-w-sm">
      <p class="text-sm text-gray-600">Log in with the seeded accounts (employee/manager/admin).</p>
      <label class="block">
        <span class="text-sm">Username</span>
        <input v-model="username" class="border rounded p-2 w-full" autocomplete="username">
      </label>
      <label class="block">
        <span class="text-sm">Password</span>
        <input v-model="password" type="password" class="border rounded p-2 w-full" autocomplete="current-password">
      </label>
      <button :disabled="busy" @click="doLogin" class="mt-2 px-4 py-2 rounded bg-black text-white">
        {{ busy ? 'Signing in…' : 'Sign in' }}
      </button>
    </section>

    <section v-else-if="step === 'dashboard'">
      <div class="flex items-center justify-between mb-4">
        <div class="text-sm text-gray-700">Signed in as <b>{{ user?.username }}</b></div>
        <button @click="logout(); step='login'" class="px-3 py-1 border rounded">Sign out</button>
      </div>

      <h2 class="text-xl font-semibold mb-2">Modules</h2>
      <div v-if="!modules.length" class="text-gray-500">No modules found.</div>
      <ul class="space-y-2">
        <li v-for="m in modules" :key="m.id" class="border rounded p-3 flex items-center justify-between">
          <div>
            <div class="font-medium">{{ m.title }}</div>
            <div class="text-xs text-gray-500">Skill: {{ m.skill }} | Pass mark: {{ m.pass_mark ?? m.passing_score }}</div>
          </div>
          <button :disabled="busy" @click="startAttempt(m)" class="px-3 py-1 rounded bg-black text-white">Start</button>
        </li>
      </ul>
    </section>

    <section v-else-if="step === 'attempt' && startPayload" class="space-y-4">
      <h2 class="text-xl font-semibold">Attempt</h2>
      <div v-for="q in startPayload.questions" :key="q.id" class="border rounded p-3">
        <div class="font-medium">{{ q.text }}</div>
        <div class="mt-2 space-y-1">
          <label v-for="c in q.choices" :key="c.id" class="flex items-center gap-2">
            <input
              :type="(q.qtype === 'single' || q.qtype === 'truefalse') ? 'radio' : 'checkbox'"
              :name="q.id"
              :value="c.id"
              :checked="answers[q.id]?.includes(c.id)"
              @change="toggleChoice(q.id, c.id, q.qtype)"
            />
            <span>{{ c.text }}</span>
          </label>
        </div>
      </div>

      <div class="flex gap-2">
        <button :disabled="busy" @click="submitAttempt" class="px-4 py-2 rounded bg-black text-white">Submit</button>
        <button :disabled="busy" @click="backToDashboard" class="px-4 py-2 rounded border">Cancel</button>
      </div>
    </section>

    <section v-else-if="step === 'result' && result" class="space-y-3">
      <h2 class="text-xl font-semibold">Result</h2>
      <div class="border rounded p-3">
        <div>Score: <b>{{ result.percent }}%</b> ({{ result.score }} / {{ result.max_score }})</div>
        <div>Passed: <b>{{ result.passed ? 'Yes' : 'No' }}</b></div>
      </div>
      <div class="space-y-2">
        <div class="font-medium mt-2">Feedback</div>
        <div v-for="f in result.feedback" :key="f.question_id" class="border rounded p-2">
          <div>Earned: {{ f.earned }} / {{ f.max }}</div>
          <div :class="f.correct ? 'text-green-700' : 'text-red-700'">{{ f.message }}</div>
        </div>
      </div>
      <button class="mt-2 px-4 py-2 rounded bg-black text-white" @click="backToDashboard">Back</button>
    </section>
  </div>
</template>

