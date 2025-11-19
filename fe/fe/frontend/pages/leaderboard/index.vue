<script setup lang="ts">
const { get } = useApi()

type Row = {
  rank: number
  user_id: string
  username: string
  overall_xp: number
  level: number
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<Row[]>([])

const search = ref('')

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/leaderboard/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load leaderboard')
  } finally {
    loading.value = false
  }
}

const filtered = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return rows.value
  return rows.value.filter(r =>
    r.username.toLowerCase().includes(term),
  )
})
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-4">
    <!-- Header + actions -->
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Leaderboard
        </h1>
        <p class="text-sm text-gray-600">
          Top users in your organisation by total XP.
        </p>
      </div>

      <div class="flex flex-wrap gap-2 sm:items-center">
        <input
          v-model="search"
          type="text"
          placeholder="Search by username…"
          class="border rounded px-2 py-1.5 text-xs min-w-[10rem]"
        >

        <NuxtLink
          to="/leaderboard/groups"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        >
          Teams &amp; departments
        </NuxtLink>
        <NuxtLink
        to="/leaderboard/skills"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        >
        Per-skill
        </NuxtLink>

        <NuxtLink
        to="/leaderboard/roles"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        >
        Per-role
        </NuxtLink>

        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </div>

    <!-- Body states -->
    <div v-if="loading" class="text-sm text-gray-500">
      Loading leaderboard…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="filtered.length === 0" class="text-sm text-gray-600">
        No users match your search yet.
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
              v-for="row in filtered"
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

    <!-- Debug payload -->
    <section class="space-y-1 text-[10px] text-gray-500">
      <div class="font-semibold">
        Raw leaderboard payload (debug)
      </div>
      <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(rows, null, 2) }}
      </pre>
    </section>
  </div>
</template>
