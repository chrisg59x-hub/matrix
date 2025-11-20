<script setup>
const { get } = useApi()

const loading = ref(true)
const error = ref(null)
const stats = ref(null)

// new: leaderboard snippets
const topUsers = ref([])          // from /leaderboard/
const topTeams = ref([])          // from /leaderboard/group/
const topDepartments = ref([])    // from /leaderboard/group/

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  stats.value = null
  topUsers.value = []
  topTeams.value = []
  topDepartments.value = []

  try {
    // 1) Core manager stats
    const dashboardPromise = get('/manager/dashboard/')

    // 2) Overall user leaderboard
    const leaderboardPromise = get('/leaderboard/')

    // 3) Teams & departments leaderboard
    const groupLeaderboardPromise = get('/leaderboard/group/')

    const [dashboard, leaderboardData, groupData] = await Promise.all([
      dashboardPromise,
      leaderboardPromise,
      groupLeaderboardPromise,
    ])

    stats.value = dashboard

    // ---- Top users (overall XP) ----
    const userRows = Array.isArray(leaderboardData)
      ? leaderboardData
      : (leaderboardData?.results || [])
    topUsers.value = userRows
      .slice(0, 3) // already ordered by XP desc on backend, but slice just in case
      .map(row => ({
        username: row.username,
        overall_xp: row.overall_xp,
        level: row.level,
        rank: row.rank,
      }))

    // ---- Top teams & departments ----
    const departments = Array.isArray(groupData?.departments)
      ? [...groupData.departments]
      : []
    const teams = Array.isArray(groupData?.teams)
      ? [...groupData.teams]
      : []

    // Ensure sorted by overall_xp desc, then slice top 3
    departments.sort((a, b) => (b.overall_xp || 0) - (a.overall_xp || 0))
    teams.sort((a, b) => (b.overall_xp || 0) - (a.overall_xp || 0))

    topDepartments.value = departments.slice(0, 3)
    topTeams.value = teams.slice(0, 3)
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load manager dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Manager dashboard
      </h1>
      <p class="text-sm text-gray-600">
        High-level training and XP stats for your organisation.
      </p>
    </header>

    <div class="flex justify-end">
      <button
        type="button"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading dashboard…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="stats" class="space-y-6">
      <!-- Core stats cards -->
      <section class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Users
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_users }}
          </div>
          <div class="text-xs text-gray-500">
            Active modules: <b>{{ stats.active_modules }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Attempts
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_attempts }}
          </div>
          <div class="text-xs text-gray-500">
            Last 30 days: <b>{{ stats.attempts_last_30_days }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Pass rate
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.pass_rate }}%
          </div>
          <div class="text-xs text-gray-500">
            Passes: <b>{{ stats.pass_count }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            XP total
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_xp }}
          </div>
          <div class="text-xs text-gray-500">
            Overall XP recorded
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Average score
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.avg_score }}%
          </div>
          <div class="text-xs text-gray-500">
            Across all attempts
          </div>
        </div>
      </section>

      <!-- NEW: Top 3 users / teams / departments -->
      <section class="grid gap-4 md:grid-cols-3">
        <!-- Top users -->
        <div class="bg-white rounded-xl shadow p-4 space-y-2">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Top users (XP)
          </div>
          <div v-if="!topUsers.length" class="text-xs text-gray-500">
            No XP recorded yet.
          </div>
          <ul v-else class="space-y-1 text-sm">
            <li
              v-for="u in topUsers"
              :key="u.user_id || u.username"
              class="flex items-center justify-between"
            >
              <div>
                <span class="font-semibold">#{{ u.rank }}</span>
                <span class="ml-2">{{ u.username }}</span>
              </div>
              <div class="text-xs text-gray-600 text-right">
                <div>{{ u.overall_xp }} XP</div>
                <div>Lvl {{ u.level }}</div>
              </div>
            </li>
          </ul>
          <NuxtLink
            to="/leaderboard"
            class="inline-flex items-center mt-2 text-xs text-emerald-700 hover:underline"
          >
            View full leaderboard
          </NuxtLink>
        </div>

        <!-- Top teams -->
        <div class="bg-white rounded-xl shadow p-4 space-y-2">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Top teams
          </div>
          <div v-if="!topTeams.length" class="text-xs text-gray-500">
            No teams with XP yet.
          </div>
          <ul v-else class="space-y-1 text-sm">
            <li
              v-for="(t, idx) in topTeams"
              :key="t.team_id || t.team_name"
              class="flex items-center justify-between"
            >
              <div>
                <span class="font-semibold">#{{ idx + 1 }}</span>
                <span class="ml-2">{{ t.team_name }}</span>
                <div v-if="t.department_name" class="text-[11px] text-gray-500">
                  {{ t.department_name }}
                </div>
              </div>
              <div class="text-xs text-gray-600 text-right">
                <div>{{ t.overall_xp }} XP</div>
                <div>Lvl {{ t.level }}</div>
              </div>
            </li>
          </ul>
          <NuxtLink
            to="/leaderboard/groups"
            class="inline-flex items-center mt-2 text-xs text-emerald-700 hover:underline"
          >
            Teams &amp; departments leaderboard
          </NuxtLink>
        </div>

        <!-- Top departments -->
        <div class="bg-white rounded-xl shadow p-4 space-y-2">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Top departments
          </div>
          <div v-if="!topDepartments.length" class="text-xs text-gray-500">
            No departments with XP yet.
          </div>
          <ul v-else class="space-y-1 text-sm">
            <li
              v-for="(d, idx) in topDepartments"
              :key="d.department_id || d.department_name || idx"
              class="flex items-center justify-between"
            >
              <div>
                <span class="font-semibold">#{{ idx + 1 }}</span>
                <span class="ml-2">
                  {{ d.department_name || 'Unassigned / No department' }}
                </span>
              </div>
              <div class="text-xs text-gray-600 text-right">
                <div>{{ d.overall_xp }} XP</div>
                <div>Lvl {{ d.level }}</div>
              </div>
            </li>
          </ul>
          <NuxtLink
            to="/leaderboard/groups"
            class="inline-flex items-center mt-2 text-xs text-emerald-700 hover:underline"
          >
            View group leaderboard
          </NuxtLink>
          <NuxtLink
            to="/manager/badges"
            class="inline-flex items-center mt-2 text-xs text-emerald-700 hover:underline"
          >
            View badge rules
          </NuxtLink>
        </div>
      </section>

      <!-- Raw stats debug -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(stats, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
