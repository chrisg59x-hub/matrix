<!-- frontend/pages/manager/signoffs.vue -->
<script setup lang="ts">
const { get } = useApi()

type Signoff = {
  id: string | number
  user: string | number
  user_name: string
  skill: string | number
  skill_name: string
  supervisor: string | number
  supervisor_name: string
  note: string | null
  created_at: string
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<Signoff[]>([])
const search = ref('')

// simple client-side filter on user/skill/supervisor/note
const filtered = computed(() => {
  if (!search.value.trim()) return rows.value
  const q = search.value.toLowerCase()
  return rows.value.filter(s =>
    (s.user_name || '').toLowerCase().includes(q) ||
    (s.skill_name || '').toLowerCase().includes(q) ||
    (s.supervisor_name || '').toLowerCase().includes(q) ||
    (s.note || '').toLowerCase().includes(q),
  )
})

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/signoffs/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load sign-offs')
  } finally {
    loading.value = false
  }
}

function formatDateTime (value: string | null) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })}`
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
    <div>
        <h1 class="text-2xl font-bold">
        Supervisor sign-offs
        </h1>
        <p class="text-sm text-gray-600">
        Records of manager/supervisor validations for skills and training.
        </p>
    </div>

    <div class="flex flex-wrap gap-2 items-center">
        <input
        v-model="search"
        type="text"
        placeholder="Filter by user, skill, supervisor, note…"
        class="border rounded px-2 py-1.5 text-sm min-w-[220px]"
        >

        <NuxtLink
        to="/manager/signoffs/new"
        class="px-3 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700"
        >
        New sign-off
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


    <!-- States -->
    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading supervisor sign-offs…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <!-- Table -->
    <div v-else>
      <div v-if="filtered.length === 0" class="text-sm text-gray-600">
        No sign-offs found yet.
      </div>

      <div
        v-else
        class="overflow-x-auto bg-white border rounded-xl shadow-sm"
      >
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">User</th>
              <th class="px-3 py-2 text-left">Skill</th>
              <th class="px-3 py-2 text-left">Supervisor</th>
              <th class="px-3 py-2 text-left">Note</th>
              <th class="px-3 py-2 text-left">Created</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="s in filtered"
              :key="s.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                {{ s.user_name }}
              </td>
              <td class="px-3 py-2">
                {{ s.skill_name }}
              </td>
              <td class="px-3 py-2">
                {{ s.supervisor_name }}
              </td>
              <td class="px-3 py-2 max-w-xs">
                <span class="line-clamp-2">
                  {{ s.note || '—' }}
                </span>
              </td>
              <td class="px-3 py-2">
                {{ formatDateTime(s.created_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
