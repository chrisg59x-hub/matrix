<script setup>
const { get } = useApi()

const loading = ref(true)
const error = ref(null)
const stats = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  try {
    stats.value = await get('/manager/dashboard/')
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load manager dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Manager dashboard
      </h1>
      <p class="text-sm text-gray-600">
        High-level training and XP stats for your organisation.
      </p>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading dashboard…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="stats" class="space-y-4">
      <section class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Users
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_users }}
          </div>
          <div class="text-xs text-gray-500">
            Active modules: <b>{{ stats.active_modules }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Attempts
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_attempts }}
          </div>
          <div class="text-xs text-gray-500">
            Last 30 days: <b>{{ stats.attempts_last_30_days }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Pass rate
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.pass_rate }}%
          </div>
          <div class="text-xs text-gray-500">
            Passes: <b>{{ stats.pass_count }}</b>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            XP total
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.total_xp }}
          </div>
          <div class="text-xs text-gray-500">
            Overall XP recorded
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Average score
          </div>
          <div class="text-2xl font-semibold">
            {{ stats.avg_score }}%
          </div>
          <div class="text-xs text-gray-500">
            Across all attempts
          </div>
        </div>
      </section>

      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(stats, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
