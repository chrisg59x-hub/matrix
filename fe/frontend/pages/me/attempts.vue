<!-- frontend/pages/me/attempts.vue -->
<script setup lang="ts">
const { get } = useApi()
const router = useRouter()

type Attempt = {
  id: string
  module: {
    id: number
    title?: string | null
    skill?: number | null
    sop?: string | null
  } | null
  created_at: string
  completed_at: string | null
  score: number
  passed: boolean
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<Attempt[]>([])

const statusFilter = ref<'all' | 'inprogress' | 'passed' | 'failed'>('all')

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/me/module-attempts/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load attempts')
  } finally {
    loading.value = false
  }
}

function statusOf (a: Attempt) {
  if (!a.completed_at) return 'In progress'
  return a.passed ? 'Passed' : 'Failed'
}

function statusKey (a: Attempt): 'inprogress' | 'passed' | 'failed' {
  if (!a.completed_at) return 'inprogress'
  return a.passed ? 'passed' : 'failed'
}

const filtered = computed(() =>
  rows.value.filter(a => {
    if (statusFilter.value === 'all') return true
    return statusKey(a) === statusFilter.value
  })
)

// small helper to format date/time
function formatDateTime (value: string | null) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function formatScore (a: Attempt) {
  if (a.score == null || Number.isNaN(Number(a.score))) return '—'
  return `${a.score}%`
}

function goToModule (a: Attempt) {
  if (!a.module?.id) return
  router.push(`/modules/${a.module.id}`)
}

// If you already have a specific "resume attempt" route, use it here
function resumeAttempt (a: Attempt) {
  if (!a.module?.id || !a.id) return
  router.push(`/modules/${a.module.id}/attempt/${a.id}`)
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          My Attempts
        </h1>
        <p class="text-sm text-gray-600">
          View your training attempts, resume in-progress modules, and review completed ones.
        </p>
      </div>

      <div class="flex flex-wrap gap-2 sm:items-center">
        <select
          v-model="statusFilter"
          class="border rounded px-2 py-1.5 text-xs"
        >
          <option value="all">
            All statuses
          </option>
          <option value="inprogress">
            In progress
          </option>
          <option value="passed">
            Passed
          </option>
          <option value="failed">
            Failed
          </option>
        </select>

        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-sm text-gray-500">
      Loading attempts…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="filtered.length === 0" class="text-sm text-gray-600">
        No attempts match your filters yet. Start a training module to create your first attempt.
      </div>

      <div v-else class="overflow-x-auto bg-white border rounded-xl shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">Module</th>
              <th class="px-3 py-2 text-left">Status</th>
              <th class="px-3 py-2 text-right">Score</th>
              <th class="px-3 py-2 text-left">Started</th>
              <th class="px-3 py-2 text-left">Completed</th>
              <th class="px-3 py-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="a in filtered"
              :key="a.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                <div class="font-medium truncate">
                  {{ a.module?.title || `Module #${a.module?.id || '—'}` }}
                </div>
              </td>
              <td class="px-3 py-2">
                <span
                  class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
                  :class="{
                    'bg-blue-100 text-blue-700': statusKey(a) === 'inprogress',
                    'bg-emerald-100 text-emerald-700': statusKey(a) === 'passed',
                    'bg-red-100 text-red-700': statusKey(a) === 'failed',
                  }"
                >
                  {{ statusOf(a) }}
                </span>
              </td>
              <td class="px-3 py-2 text-right">
                {{ formatScore(a) }}
              </td>
              <td class="px-3 py-2">
                {{ formatDateTime(a.created_at) }}
              </td>
              <td class="px-3 py-2">
                {{ formatDateTime(a.completed_at) }}
              </td>
              <td class="px-3 py-2 text-right">
                <div class="inline-flex gap-2">
                  <NuxtLink
                    :to="`/attempts/${a.id}/review`"
                    class="text-xs text-emerald-700 hover:underline"
                  >
                    Review
                  </NuxtLink>
                  <button
                    type="button"
                    class="px-2 py-1 text-xs rounded border bg-white hover:bg-gray-50"
                    @click="goToModule(a)"
                  >
                    View module
                  </button>

                  <button
                    v-if="statusKey(a) === 'inprogress'"
                    type="button"
                    class="px-2 py-1 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
                    @click="resumeAttempt(a)"
                  >
                    Resume
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>