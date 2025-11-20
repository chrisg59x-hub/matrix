<script setup lang="ts">
const { get } = useApi()
const router = useRouter()

// ---- Types ----
type ProgressSkill = {
  skill_id: string | null
  skill_name: string | null
  xp: number
}

type ProgressPayload = {
  overall_xp: number
  overall_level: number
  next_level: number
  xp_to_next: number
  skills: ProgressSkill[]
}

type OverdueItem = {
  id: number
  skill_name?: string | null
  sop_title?: string | null
  skill_id?: number | null
  sop_id?: string | null
  due_at?: string | null
  due_date?: string | null
  reason?: string | null
}

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

// ---- State ----
const loading = ref(true)
const err = ref<string | null>(null)

const progress = ref<ProgressPayload | null>(null)
const overdue = ref<OverdueItem[]>([])
const attempts = ref<Attempt[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null

  try {
    const [p, o, a] = await Promise.all([
      get('/my_progress/'),
      get('/me/overdue-sops/'),
      get('/me/module-attempts/'),
    ])

    // Progress
    progress.value = p as ProgressPayload

    // Overdue – accept array or {results: [...]}, show top 3
    const oList: any[] = Array.isArray(o) ? o : (o?.results || [])
    overdue.value = oList.slice(0, 3)

    // Attempts – accept array or {results: [...]}, sort & slice 5
    const aList: any[] = Array.isArray(a) ? a : (a?.results || [])
    attempts.value = aList
      .sort((x, y) => {
        const tx = new Date(x.created_at).getTime()
        const ty = new Date(y.created_at).getTime()
        return ty - tx
      })
      .slice(0, 5)
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load dashboard')
  } finally {
    loading.value = false
  }
}

// ---- Helpers ----
const overallPercentToNext = computed(() => {
  if (!progress.value) return 0
  const total = progress.value.overall_xp + progress.value.xp_to_next
  if (total <= 0) return 0
  return Math.round((progress.value.overall_xp / total) * 100)
})

function formatDateTime (value: string | null) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function statusLabel (a: Attempt) {
  if (!a.completed_at) return 'In progress'
  return a.passed ? 'Passed' : 'Failed'
}

function statusClass (a: Attempt) {
  if (!a.completed_at) return 'bg-blue-100 text-blue-700'
  return a.passed ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
}

function goToModule (a: Attempt) {
  if (!a.module?.id) return
  router.push(`/modules/${a.module.id}`)
}

function goToOverdueTraining () {
  router.push('/training/overdue')
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          My Training
        </h1>
        <p class="text-sm text-gray-600">
          Overview of your XP, overdue training and recent activity.
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
        <NuxtLink
          to="/me/progress"
          class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
        >
          Detailed progress
        </NuxtLink>
      </div>
    </header>

    <!-- Error / Loading -->
    <div
      v-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div
      v-else-if="loading"
      class="p-4 rounded bg-gray-100 text-sm"
    >
      Loading your dashboard…
    </div>

    <div v-else class="space-y-6">
      <!-- Top row: Overall progress + quick overdue summary -->
      <section class="grid gap-4 md:grid-cols-3">
        <!-- Overall XP / Level -->
        <div class="md:col-span-2 bg-white rounded-xl shadow p-4 space-y-3">
          <div class="flex items-baseline justify-between">
            <div>
              <div class="text-xs text-gray-500 uppercase tracking-wide">
                Overall progress
              </div>
              <div class="text-2xl font-semibold">
                Level {{ progress?.overall_level ?? 0 }}
              </div>
            </div>
            <div class="text-right text-xs text-gray-600">
              <div>
                XP: <span class="font-semibold">{{ progress?.overall_xp ?? 0 }}</span>
              </div>
              <div>
                To next level:
                <span class="font-semibold">{{ progress?.xp_to_next ?? 0 }}</span>
              </div>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
            <div
              class="h-3 rounded-full bg-emerald-500 transition-all"
              :style="{ width: `${overallPercentToNext}%` }"
            />
          </div>
          <div class="text-xs text-gray-500">
            {{ overallPercentToNext }}% of current level completed.
          </div>

          <!-- Key skills list -->
          <div v-if="progress && progress.skills && progress.skills.length" class="mt-2">
            <div class="text-xs font-semibold text-gray-600 mb-1">
              Top skills
            </div>
            <div class="flex flex-wrap gap-2 text-xs">
              <span
                v-for="s in progress.skills.slice(0, 4)"
                :key="String(s.skill_id) + String(s.skill_name)"
                class="inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5"
              >
                <span class="font-medium">
                  {{ s.skill_name || 'Unnamed skill' }}
                </span>
                <span class="ml-2 text-[11px]">
                  {{ s.xp }} XP
                </span>
              </span>
            </div>
          </div>
        </div>

        <!-- Overdue summary card -->
        <div class="bg-white rounded-xl shadow p-4 space-y-2">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-xs text-gray-500 uppercase tracking-wide">
                Overdue training
              </div>
              <div class="text-2xl font-semibold">
                {{ overdue.length }}
              </div>
            </div>
            <button
              type="button"
              class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
              @click="goToOverdueTraining"
            >
              View all
            </button>
          </div>

          <p class="text-xs text-gray-600">
            These are training items that have passed their due date.
          </p>

          <ul v-if="overdue.length" class="space-y-1 text-xs">
            <li
              v-for="item in overdue"
              :key="item.id"
              class="flex justify-between items-start gap-2"
            >
              <div class="flex-1 min-w-0">
                <div class="font-medium truncate">
                  {{ item.skill_name || 'Unspecified skill' }}
                </div>
                <div v-if="item.sop_title" class="text-[11px] text-gray-500 truncate">
                  SOP: {{ item.sop_title }}
                </div>
                <div class="text-[11px] text-gray-500">
                  Reason: {{ item.reason || 'Not specified' }}
                </div>
              </div>
              <div class="text-[11px] text-right text-gray-500 min-w-[5rem]">
                Due
                <div class="font-medium">
                  {{ formatDateTime(item.due_at || item.due_date || null) }}
                </div>
              </div>
            </li>
          </ul>

          <div v-else class="text-xs text-emerald-700">
            ✅ You have no overdue training. Great work!
          </div>
        </div>
      </section>

      <!-- Recent attempts -->
      <section class="bg-white rounded-xl shadow p-4 space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm font-semibold text-gray-700">
              Recent attempts
            </div>
            <p class="text-xs text-gray-500">
              Your last few training attempts.
            </p>
          </div>
          <NuxtLink
            to="/me/attempts"
            class="text-xs text-emerald-700 hover:underline"
          >
            View all attempts
          </NuxtLink>
        </div>

        <div v-if="attempts.length === 0" class="text-sm text-gray-500">
          No attempts yet. Start a module from the <NuxtLink to="/modules" class="text-emerald-700 hover:underline">Modules</NuxtLink> page.
        </div>

        <div
          v-else
          class="overflow-x-auto -mx-2"
        >
          <table class="min-w-full text-xs border-collapse">
            <thead>
              <tr class="bg-gray-50 border-b text-[11px] text-gray-500 uppercase tracking-wide">
                <th class="text-left py-2 px-3">Module</th>
                <th class="text-left py-2 px-3">Status</th>
                <th class="text-right py-2 px-3">Score</th>
                <th class="text-left py-2 px-3">Started</th>
                <th class="text-left py-2 px-3">Completed</th>
                <th class="text-right py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="a in attempts"
                :key="a.id"
                class="border-b hover:bg-gray-50"
              >
                <td class="py-1.5 px-3">
                  <div class="font-medium truncate max-w-xs">
                    {{ a.module?.title || `Module #${a.module?.id || '—'}` }}
                  </div>
                </td>
                <td class="py-1.5 px-3">
                  <span
                    class="inline-flex items-center rounded-full px-2 py-0.5"
                    :class="statusClass(a)"
                  >
                    {{ statusLabel(a) }}
                  </span>
                </td>
                <td class="py-1.5 px-3 text-right">
                  <span v-if="a.completed_at">
                    {{ a.score }}%
                  </span>
                  <span v-else>
                    —
                  </span>
                </td>
                <td class="py-1.5 px-3">
                  {{ formatDateTime(a.created_at) }}
                </td>
                <td class="py-1.5 px-3">
                  {{ formatDateTime(a.completed_at) }}
                </td>
                <td class="py-1.5 px-3 text-right">
                  <div class="inline-flex gap-2">
                    <button
                      type="button"
                      class="px-2 py-1 rounded border bg-white hover:bg-gray-50"
                      @click="goToModule(a)"
                    >
                      View module
                    </button>
                    <NuxtLink
                      :to="`/attempts/${a.id}/review`"
                      class="px-2 py-1 rounded border bg-white hover:bg-gray-50"
                    >
                      Review
                    </NuxtLink>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

