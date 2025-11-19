<script setup lang="ts">
const { get } = useApi()

type UserRow = {
  id: string
  username: string
  email: string | null
  org: string | number | null
  org_name?: string | null
  biz_role?: string | null
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<UserRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/users/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load users')
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
          Users
        </h1>
        <p class="text-sm text-gray-600">
          All users in your organisation.
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
      Loading users…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No users found.
      </div>

      <div v-else class="overflow-x-auto bg-white border rounded-xl shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">Username</th>
              <th class="px-3 py-2 text-left">Email</th>
              <th class="px-3 py-2 text-left">Org</th>
              <th class="px-3 py-2 text-left">Role</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="u in rows"
              :key="u.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                {{ u.username }}
              </td>
              <td class="px-3 py-2">
                {{ u.email || '—' }}
              </td>
              <td class="px-3 py-2">
                {{ u.org_name || u.org || '—' }}
              </td>
              <td class="px-3 py-2">
                {{ u.biz_role || '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
