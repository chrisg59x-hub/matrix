<script setup lang="ts">
const { get } = useApi()

type Skill = {
  id: string
  name: string
}

type Row = {
  rank: number
  user_id: string
  username: string
  overall_xp: number
  level: number
}

const loading = ref(true)
const err = ref<string | null>(null)

const skills = ref<Skill[]>([])
const selectedSkillId = ref<string | null>(null)
const rows = ref<Row[]>([])

onMounted(async () => {
  await loadSkills()
})

async function loadSkills () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/skills/')
    const list = Array.isArray(data) ? data : (data.results || [])
    skills.value = list
    if (!selectedSkillId.value && skills.value.length > 0) {
      selectedSkillId.value = String(skills.value[0].id)
      await loadLeaderboard()
    } else {
      loading.value = false
    }
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load skills')
    loading.value = false
  }
}

async function loadLeaderboard () {
  if (!selectedSkillId.value) return
  loading.value = true
  err.value = null
  try {
    // 👇 use your existing backend route
    const data: any = await get(`/leaderboard/skill/${selectedSkillId.value}/`)
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load skill leaderboard')
  } finally {
    loading.value = false
  }
}

const selectedSkill = computed(() =>
  skills.value.find(s => String(s.id) === selectedSkillId.value) || null,
)
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-4">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Skill leaderboard
        </h1>
        <p class="text-sm text-gray-600">
          XP leaderboard filtered to a specific skill.
        </p>
      </div>

      <div class="flex flex-wrap gap-2 sm:items-center">
        <NuxtLink
          to="/leaderboard"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        >
          Overall leaderboard
        </NuxtLink>

        <NuxtLink
          to="/leaderboard/groups"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        >
          Teams &amp; departments
        </NuxtLink>
      </div>
    </div>

    <!-- Skill selector -->
    <div class="flex flex-wrap gap-2 items-center">
      <label class="text-xs text-gray-600">
        Skill:
      </label>
      <select
        v-model="selectedSkillId"
        class="border rounded px-2 py-1.5 text-xs min-w-[12rem]"
        @change="loadLeaderboard"
      >
        <option
          v-for="s in skills"
          :key="s.id"
          :value="String(s.id)"
        >
          {{ s.name }}
        </option>
      </select>

      <button
        type="button"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        @click="loadLeaderboard"
      >
        Refresh
      </button>
    </div>

    <p v-if="selectedSkill" class="text-xs text-gray-500">
      Showing XP for skill:
      <span class="font-semibold">{{ selectedSkill.name }}</span>
    </p>

    <!-- States -->
    <div v-if="loading" class="text-sm text-gray-500">
      Loading skill leaderboard…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No XP records yet for this skill.
      </div>

      <div
        v-else
        class="overflow-x-auto bg-white border rounded-xl shadow-sm"
      >
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">Rank</th>
              <th class="px-3 py-2 text-left">User</th>
              <th class="px-3 py-2 text-right">XP</th>
              <th class="px-3 py-2 text-right">Level</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="row in rows"
              :key="row.user_id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                #{{ row.rank }}
              </td>
              <td class="px-3 py-2">
                {{ row.username }}
              </td>
              <td class="px-3 py-2 text-right">
                {{ row.overall_xp }}
              </td>
              <td class="px-3 py-2 text-right">
                {{ row.level }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Debug -->
    <section class="space-y-1 text-[10px] text-gray-500">
      <div class="font-semibold">
        Raw skill leaderboard payload (debug)
      </div>
      <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(rows, null, 2) }}
      </pre>
    </section>
  </div>
</template>
