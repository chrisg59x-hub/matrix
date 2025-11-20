<!-- frontend/pages/leaderboard/groups.vue -->
<script setup lang="ts">
const { get } = useApi()

type DepartmentRow = {
  department_id: string | null
  department_name: string | null
  overall_xp: number
  level: number
}

type TeamRow = {
  team_id: string
  team_name: string
  department_id: string | null
  department_name: string | null
  overall_xp: number
  level: number
}

type Payload = {
  departments: DepartmentRow[]
  teams: TeamRow[]
}

const loading = ref(true)
const err = ref<string | null>(null)
const data = ref<Payload | null>(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const resp: any = await get('/leaderboard/group/')
    data.value = resp
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load group leaderboard')
  } finally {
    loading.value = false
  }
}

// sorted departments by XP desc
const departments = computed<DepartmentRow[]>(() => {
  const rows = data.value?.departments || []
  return [...rows].sort((a, b) => (b.overall_xp || 0) - (a.overall_xp || 0))
})

// sorted teams by XP desc
const teams = computed<TeamRow[]>(() => {
  const rows = data.value?.teams || []
  return [...rows].sort((a, b) => (b.overall_xp || 0) - (a.overall_xp || 0))
})

function formatNumber (n: number | null | undefined) {
  if (n == null || Number.isNaN(Number(n))) return '0'
  return Number(n).toLocaleString()
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Team &amp; Department Leaderboard
        </h1>
        <p class="text-sm text-gray-600">
          XP totals grouped by department and team within your organisation.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <NuxtLink
          to="/leaderboard"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        >
          Back to user leaderboard
        </NuxtLink>

        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading group leaderboard…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else-if="data" class="space-y-6">
      <!-- Departments -->
      <section>
        <h2 class="text-sm font-semibold text-gray-800 mb-2">
          Departments
        </h2>

        <div v-if="!departments.length" class="text-sm text-gray-600">
          No departments found or no XP recorded yet.
        </div>

        <div
          v-else
          class="overflow-x-auto bg-white border rounded-xl shadow-sm"
        >
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th class="px-3 py-2 text-left">
                  Rank
                </th>
                <th class="px-3 py-2 text-left">
                  Department
                </th>
                <th class="px-3 py-2 text-right">
                  XP
                </th>
                <th class="px-3 py-2 text-right">
                  Level
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="(d, idx) in departments"
                :key="d.department_id || d.department_name || `dept-${idx}`"
                class="hover:bg-gray-50"
              >
                <td class="px-3 py-2">
                  #{{ idx + 1 }}
                </td>
                <td class="px-3 py-2">
                  {{ d.department_name || 'Unassigned / No department' }}
                </td>
                <td class="px-3 py-2 text-right">
                  {{ formatNumber(d.overall_xp) }}
                </td>
                <td class="px-3 py-2 text-right">
                  L{{ d.level }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Teams -->
      <section>
        <h2 class="text-sm font-semibold text-gray-800 mb-2">
          Teams
        </h2>

        <div v-if="!teams.length" class="text-sm text-gray-600">
          No teams found or no XP recorded yet.
        </div>

        <div
          v-else
          class="overflow-x-auto bg-white border rounded-xl shadow-sm"
        >
          <table class="min-w-full text-sm">
            <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th class="px-3 py-2 text-left">
                  Rank
                </th>
                <th class="px-3 py-2 text-left">
                  Team
                </th>
                <th class="px-3 py-2 text-left">
                  Department
                </th>
                <th class="px-3 py-2 text-right">
                  XP
                </th>
                <th class="px-3 py-2 text-right">
                  Level
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr
                v-for="(t, idx) in teams"
                :key="t.team_id || `team-${idx}`"
                class="hover:bg-gray-50"
              >
                <td class="px-3 py-2">
                  #{{ idx + 1 }}
                </td>
                <td class="px-3 py-2">
                  {{ t.team_name }}
                </td>
                <td class="px-3 py-2">
                  {{ t.department_name || '—' }}
                </td>
                <td class="px-3 py-2 text-right">
                  {{ formatNumber(t.overall_xp) }}
                </td>
                <td class="px-3 py-2 text-right">
                  L{{ t.level }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Debug payload -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw group leaderboard payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(data, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
