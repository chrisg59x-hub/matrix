<script setup>
const { get } = useApi()

const loading = ref(true)
const error = ref(null)
const progress = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  try {
    // Adjust this path if your backend URL is different
    progress.value = await get('/my-progress/')
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load progress')
  } finally {
    loading.value = false
  }
}

const skillsSorted = computed(() => {
  if (!progress.value || !Array.isArray(progress.value.skills)) return []
  return [...progress.value.skills].sort((a, b) => (b.xp || 0) - (a.xp || 0))
})
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          My progress
        </h1>
        <p class="text-sm text-gray-600">
          XP and level details for your training.
        </p>
      </div>
      <NuxtLink
        to="/me/dashboard"
        class="px-3 py-1.5 rounded bg-gray-900 text-white text-xs hover:bg-black"
      >
        Go to my dashboard
      </NuxtLink>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading your progress…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="progress" class="space-y-6">
      <!-- XP & level summary -->
      <section class="grid gap-4 sm:grid-cols-3">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Overall XP
          </div>
          <div class="text-2xl font-semibold">
            {{ progress.overall_xp }}
          </div>
          <div class="text-xs text-gray-500">
            Towards level {{ progress.next_level }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Level
          </div>
          <div class="text-2xl font-semibold">
            {{ progress.overall_level }}
          </div>
          <div class="text-xs text-gray-500">
            Next level: {{ progress.next_level }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            XP to next level
          </div>
          <div class="text-2xl font-semibold">
            {{ progress.xp_to_next }}
          </div>
          <div class="text-xs text-gray-500">
            XP needed to reach level {{ progress.next_level }}
          </div>
        </div>
      </section>

      <!-- Per-skill XP breakdown -->
      <section class="space-y-3">
        <h2 class="text-sm font-semibold text-gray-800">
          XP by skill
        </h2>

        <div
          v-if="!skillsSorted.length"
          class="p-3 rounded bg-gray-50 text-xs text-gray-700"
        >
          You don’t have any XP recorded against specific skills yet.
          Complete some training modules to see this breakdown.
        </div>

        <div
          v-else
          class="space-y-2"
        >
          <div
            v-for="s in skillsSorted"
            :key="s.skill_id || s.skill_name"
            class="bg-white rounded-xl shadow p-3 text-sm"
          >
            <div class="flex items-center justify-between mb-1">
              <div class="font-medium text-gray-900">
                {{ s.skill_name || 'Unspecified skill' }}
              </div>
              <div class="text-xs text-gray-600">
                {{ s.xp }} XP
              </div>
            </div>
            <div class="h-2 rounded bg-gray-100 overflow-hidden">
              <div
                class="h-full bg-emerald-500"
                :style="{ width: Math.min(100, (s.xp || 0) / (progress.overall_xp || 1) * 100) + '%' }"
              />
            </div>
          </div>
        </div>
      </section>

      <!-- Debug payload -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw progress payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(progress, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>

