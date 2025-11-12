<script setup lang="ts">
const { get } = useApi()
const data = ref<any|null>(null)
onMounted(async()=>{ data.value = await get('/me/progress/') })
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">My Progress</h1>
    <div v-if="!data" class="text-gray-500">Loading…</div>
    <div v-else class="space-y-2">
      <div>Overall XP: <b>{{ data.overall_xp }}</b></div>
      <div>Level: <b>{{ data.overall_level }}</b> → Next: {{ data.next_level }} ({{ data.xp_to_next }} XP to go)</div>
      <div class="mt-3">
        <h2 class="font-semibold">Skills</h2>
        <ul class="list-disc ml-5">
          <li v-for="s in data.skills" :key="s.skill_id">{{ s.skill_name }} — {{ s.xp }} XP</li>
        </ul>
      </div>
    </div>
  </div>
</template>
