<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold">Leaderboards</h1>
        <p class="text-sm text-gray-500">
          XP & Levels for your organisation. Filter by skill or role, and export CSVs.
        </p>
      </div>
      <NuxtLink
          to="/leaderboard/groups"
          class="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-100"
        >
          Teams &amp; departments leaderboard
        </NuxtLink>

      <div class="flex flex-wrap gap-2">
        <button
          class="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-100"
          @click="downloadLeaderboardCsv"
        >
          Download leaderboard CSV
        </button>

        <button
          class="px-3 py-1.5 text-sm rounded border border-gray-300 hover:bg-gray-100"
          @click="downloadXpCsv"
        >
          Download XP log CSV
        </button>
      </div>
    </header>

    <!-- Mode Selector -->
    <section class="bg-white rounded-lg shadow-sm border p-4 space-y-4">
      <div class="flex flex-wrap items-center gap-4">
        <label class="inline-flex items-center gap-2 text-sm">
          <input type="radio" value="org" v-model="mode" class="accent-emerald-600" />
          <span>Org leaderboard</span>
        </label>

        <label class="inline-flex items-center gap-2 text-sm">
          <input type="radio" value="skill" v-model="mode" class="accent-emerald-600" />
          <span>By skill</span>
        </label>

        <label class="inline-flex items-center gap-2 text-sm">
          <input type="radio" value="role" v-model="mode" class="accent-emerald-600" />
          <span>By role</span>
        </label>
      </div>

      <!-- Skill/Role Filters -->
      <div v-if="mode !== 'org'" class="flex flex-wrap gap-4">
        <div v-if="mode === 'skill'" class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500">Skill</label>
          <select
            v-model="selectedSkillId"
            class="border rounded px-2 py-1 text-sm min-w-[200px]"
          >
            <option :value="null">Select a skill…</option>
            <option v-for="sk in skills" :key="sk.id" :value="sk.id">{{ sk.name }}</option>
          </select>
        </div>

        <div v-if="mode === 'role'" class="flex flex-col gap-1">
          <label class="text-xs font-medium text-gray-500">Role</label>
          <select
            v-model="selectedRoleId"
            class="border rounded px-2 py-1 text-sm min-w-[200px]"
          >
            <option :value="null">Select a role…</option>
            <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>

        <button
          class="self-end px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
          :disabled="mode !== 'org' && !canLoadFiltered"
          @click="loadLeaderboard"
        >
          Refresh
        </button>
      </div>
    </section>

    <!-- Leaderboard Table -->
    <section class="bg-white rounded-lg shadow-sm border p-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-sm font-semibold text-gray-700">{{ leaderboardTitle }}</h2>
        <span v-if="isLoading" class="text-xs text-gray-400">Loading…</span>
      </div>

      <div v-if="error" class="text-sm text-red-600 mb-3">{{ error }}</div>

      <div v-if="entries.length === 0 && !isLoading" class="text-sm text-gray-500">
        No XP data available yet.
      </div>

      <div v-else class="overflow-x-auto">
        <table class="min-w-full text-sm border-collapse">
          <thead>
            <tr class="bg-gray-50 border-b">
              <th class="text-left py-2 px-3">Rank</th>
              <th class="text-left py-2 px-3">User</th>
              <th class="text-right py-2 px-3">XP</th>
              <th class="text-right py-2 px-3">Level</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="row in entries"
              :key="row.user_id + '-' + row.rank"
              class="border-b hover:bg-gray-50"
            >
              <td class="py-1.5 px-3">{{ row.rank }}</td>
              <td class="py-1.5 px-3">{{ row.username }}</td>
              <td class="py-1.5 px-3 text-right">{{ row.overall_xp }}</td>
              <td class="py-1.5 px-3 text-right">{{ row.level }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
const mode = ref("org")
const entries = ref([])
const skills = ref([])
const roles = ref([])
const selectedSkillId = ref(null)
const selectedRoleId = ref(null)
const isLoading = ref(false)
const error = ref("")
const xpSinceDays = ref(30)

const { public: publicRuntime } = useRuntimeConfig()
const apiBase = publicRuntime.apiBase || "/api"

const auth = useAuth()
const token = computed(() => auth.token?.value || auth.token || null)

const canLoadFiltered = computed(() => {
  if (mode.value === "skill") return !!selectedSkillId.value
  if (mode.value === "role") return !!selectedRoleId.value
  return true
})

const leaderboardTitle = computed(() => {
  if (mode.value === "org") return "Organisation leaderboard"
  if (mode.value === "skill") {
    const s = skills.value.find((x) => x.id === selectedSkillId.value)
    return s ? `Skill: ${s.name}` : "Skill leaderboard"
  }
  if (mode.value === "role") {
    const r = roles.value.find((x) => x.id === selectedRoleId.value)
    return r ? `Role: ${r.name}` : "Role leaderboard"
  }
  return "Leaderboard"
})

async function authorisedFetch(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (token.value) headers.set("Authorization", `Bearer ${token.value}`)
  return fetch(`${apiBase}${path}`, { ...options, headers })
}

async function loadLeaderboard() {
  isLoading.value = true
  error.value = ""

  try {
    let path = "/leaderboard/"
    if (mode.value === "skill") path = `/leaderboard/skill/${selectedSkillId.value}/`
    if (mode.value === "role") path = `/leaderboard/role/${selectedRoleId.value}/`

    const res = await authorisedFetch(path)
    if (!res.ok) throw new Error("Failed to load leaderboard")

    entries.value = await res.json()
  } catch (err) {
    error.value = err.message
    entries.value = []
  } finally {
    isLoading.value = false
  }
}

async function loadSkillsAndRoles() {
  try {
    const resSkills = await authorisedFetch("/skills/")
    const dS = await resSkills.json()
    skills.value = dS.results || dS || []
  } catch (_) {}

  try {
    const resRoles = await authorisedFetch("/roles/")
    const dR = await resRoles.json()
    roles.value = dR.results || dR || []
  } catch (_) {}
}

async function downloadCsv(path, filename) {
  const headers = new Headers()
  if (token.value) headers.set("Authorization", `Bearer ${token.value}`)

  const res = await fetch(`${apiBase}${path}`, { headers })
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function downloadLeaderboardCsv() {
  downloadCsv("/leaderboard.csv", "leaderboard.csv")
}

function downloadXpCsv() {
  downloadCsv(`/xp/export.csv?since_days=${xpSinceDays.value}`, "xp_events.csv")
}

onMounted(async () => {
  await loadSkillsAndRoles()
  await loadLeaderboard()
})
</script>
