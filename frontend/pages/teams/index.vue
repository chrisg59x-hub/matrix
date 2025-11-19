<script setup lang="ts">
const { get } = useApi()

type TeamRow = {
  id: string
  org: string | number
  department?: string | number | null
  department_name?: string | null
  name: string
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<TeamRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/teams/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load teams')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-4">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Teams
        </h1>
        <p class="text-sm text-gray-600">
          Teams within your organisation.
        </p>
      </div>

      <button
        type="button"
        class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="text-sm text-gray-500">
      Loading teams…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No teams found.
      </div>

      <div v-else class="overflow-x-auto bg-white border rounded-xl shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">Team</th>
              <th class="px-3 py-2 text-left">Department</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="t in rows"
              :key="t.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                {{ t.name }}
              </td>
              <td class="px-3 py-2">
                {{ t.department_name || '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
