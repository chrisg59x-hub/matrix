<script setup lang="ts">
const { get, post } = useApi()
const modules = ref<any[]>([])
const busy = ref(false)
const err = ref<string | null>(null)
const started = ref<any|null>(null)
const answers = ref<Record<string, string[]>>({})
const result = ref<any|null>(null)

onMounted(load)
async function load() {
  const data:any = await get('/modules/')
  modules.value = Array.isArray(data) ? data : (data.results || [])
}

async function startAttempt(m:any) {
  busy.value = true; err.value = null
  try {
    started.value = await post(`/modules/${m.id}/start/`, {})
    answers.value = {}
    for (const q of started.value.questions) answers.value[q.id] = []
  } catch (e:any){ err.value = e?.data?.detail || 'Could not start attempt' }
  finally { busy.value = false }
}

function toggle(qid:string,cid:string,qtype:string) {
  if (qtype==='single' || qtype==='truefalse') answers.value[qid]=[cid]
  else {
    const s = new Set(answers.value[qid]||[])
    s.has(cid)?s.delete(cid):s.add(cid)
    answers.value[qid]=[...s]
  }
}

async function submitAttempt() {
  if (!started.value) return
  const payload = { answers: Object.entries(answers.value).map(([question_id,choice_ids])=>({question_id,choice_ids})) }
  result.value = await post(`/attempts/${started.value.attempt_id}/submit/`, payload)
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">Dashboard</h1>

    <div v-if="!started">
      <h2 class="text-lg font-semibold mb-2">Modules</h2>
      <div v-if="!modules.length" class="text-gray-500">No modules found.</div>
      <ul class="space-y-2">
        <li v-for="m in modules" :key="m.id" class="border rounded p-3 flex justify-between">
          <div>
            <div class="font-medium">{{ m.title }}</div>
            <div class="text-xs text-gray-500">Pass: {{ m.pass_mark ?? m.passing_score }}</div>
          </div>
          <button @click="startAttempt(m)" class="px-3 py-1 rounded bg-black text-white">Start</button>
        </li>
      </ul>
    </div>

    <div v-else-if="started && !result" class="space-y-4">
      <h2 class="text-lg font-semibold">Attempt</h2>
      <div v-for="q in started.questions" :key="q.id" class="border rounded p-3">
        <div class="font-medium">{{ q.text }}</div>
        <div class="mt-2 space-y-1">
          <label v-for="c in q.choices" :key="c.id" class="flex gap-2">
            <input
              :type="(q.qtype==='single'||q.qtype==='truefalse')?'radio':'checkbox'"
              :name="q.id" :value="c.id" :checked="answers[q.id]?.includes(c.id)"
              @change="toggle(q.id,c.id,q.qtype)"
            />
            <span>{{ c.text }}</span>
          </label>
        </div>
      </div>
      <button @click="submitAttempt" class="px-4 py-2 rounded bg-black text-white">Submit</button>
    </div>

    <div v-else-if="result" class="space-y-3">
      <h2 class="text-lg font-semibold">Result</h2>
      <div class="border rounded p-3">Score: <b>{{ result.percent }}%</b></div>
      <div class="space-y-2">
        <div class="font-medium">Feedback</div>
        <div v-for="f in result.feedback" :key="f.question_id" class="border rounded p-2">
          <div>{{ f.earned }} / {{ f.max }} — <b>{{ f.correct ? 'Correct' : 'Incorrect' }}</b></div>
          <div class="text-sm text-gray-700">{{ f.message }}</div>
        </div>
      </div>
      <div class="flex gap-2">
        <button @click="started=null; result=null" class="border rounded px-3 py-1">Back</button>
      </div>
    </div>

    <p v-if="err" class="text-red-600">{{ err }}</p>
  </div>
</template>
