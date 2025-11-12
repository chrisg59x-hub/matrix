<script setup lang="ts">
const { get, post } = useApi()
const { user } = useAuth()
const canEdit = computed(() => ['manager','admin'].includes(user.value?.biz_role || ''))
const rows = ref<any[]>([])
const form = ref({ level: 1, total_xp: 0 })
const loading = ref(false); const err = ref<string|null>(null)

onMounted(load)
async function load() {
  const data:any = await get('/levels/')
  rows.value = Array.isArray(data) ? data : (data.results || [])
}
async function addLevel() {
  if (!canEdit.value) return
  loading.value = true; err.value = null
  try {
    await post('/levels/', form.value)
    form.value = { level: 1, total_xp: 0 }
    await load()
  } catch (e:any) { err.value = e?.data?.detail || 'Save failed' }
  finally { loading.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">Level Definitions</h1>
    <p v-if="!canEdit" class="text-red-600">Manager or Admin only.</p>

    <section class="max-w-lg">
      <h2 class="text-lg font-semibold mb-2">Add Level</h2>
      <div class="grid grid-cols-2 gap-2">
        <input v-model.number="form.level" type="number" min="1" class="border rounded p-2" placeholder="Level" />
        <input v-model.number="form.total_xp" type="number" min="0" class="border rounded p-2" placeholder="Total XP" />
      </div>
      <div class="mt-2">
        <button :disabled="!canEdit || loading" class="px-3 py-1 rounded bg-black text-white" @click="addLevel">
          {{ loading ? 'Saving…' : 'Save' }}
        </button>
        <span v-if="err" class="text-red-600 ml-2">{{ err }}</span>
      </div>
    </section>

    <section>
      <h2 class="text-lg font-semibold mb-2">Current</h2>
      <table class="w-full border max-w-md">
        <thead><tr class="bg-gray-50">
          <th class="p-2 text-left">Level</th>
          <th class="p-2 text-left">Total XP</th>
        </tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id" class="border-t">
            <td class="p-2">{{ r.level }}</td>
            <td class="p-2">{{ r.total_xp }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>
