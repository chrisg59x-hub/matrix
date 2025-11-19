<script setup lang="ts">
const { get } = useApi()

type DepartmentRow = {
  id: string
  org: string | number
  name: string
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<DepartmentRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/departments/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load departments')
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
          Departments
        </h1>
        <p class="text-sm text-gray-600">
          Departments in your organisation.
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
      Loading departments…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No departments found.
      </div>

      <div v-else class="overflow-x-auto bg-white border rounded-xl shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">Department</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="d in rows"
              :key="d.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                {{ d.name }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
