<script setup lang="ts">
const { get } = useApi()
const rows = ref<any[]>([])
onMounted(async()=>{ rows.value = await get('/leaderboard/') })
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Leaderboard</h1>
    <div v-if="!rows.length" class="text-gray-500">No entries yet.</div>
    <table v-else class="w-full border">
      <thead><tr class="bg-gray-50">
        <th class="text-left p-2">Rank</th>
        <th class="text-left p-2">User</th>
        <th class="text-left p-2">XP</th>
        <th class="text-left p-2">Level</th>
      </tr></thead>
      <tbody>
        <tr v-for="r in rows" :key="r.user_id" class="border-t">
          <td class="p-2">{{ r.rank }}</td>
          <td class="p-2">{{ r.username }}</td>
          <td class="p-2">{{ r.overall_xp }}</td>
          <td class="p-2">{{ r.level }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
