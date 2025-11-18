<script setup>
const route = useRoute()
const { get } = useApi()

const moduleId = computed(() => route.params.id)

const loading = ref(true)
const error = ref(null)
const stats = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  try {
    // Call the new backend endpoint
    stats.value = await get(`/modules/${moduleId.value}/stats/`)
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load module stats')
  } finally {
    loading.value = false
  }
}

function formatDate (val) {
  if (!val) return '—'
  // naive ISO -> readable; you can wire a real date lib later
  try {
    const d = new Date(val)
    return d.toLocaleString()
  } catch {
    return String(val)
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Module stats
      </h1>
      <p class="text-sm text-gray-600">
        Analytics for this training module.
      </p>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading stats…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="stats" class="space-y-4">
      <section class="bg-white rounded-xl shadow p-4 space-y-3">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">
            {{ stats.title }}
          </h2>
          <p class="text-xs text-gray-500">
            Module ID:
            <code class="text-[10px] break-all">
              {{ stats.module_id }}
            </code>
          </p>
        </div>

        <div class="grid grid-cols-2 gap-4 text-sm">
          <div class="space-y-1">
            <div class="text-xs text-gray-500 uppercase tracking-wide">
              Attempts
            </div>
            <div class="text-xl font-semibold">
              {{ stats.total_attempts }}
            </div>
            <div class="text-xs text-gray-500">
              Unique users: <b>{{ stats.unique_users }}</b>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-xs text-gray-500 uppercase tracking-wide">
              Pass rate
            </div>
            <div class="text-xl font-semibold">
              {{ stats.pass_rate }}%
            </div>
            <div class="text-xs text-gray-500">
              Passes: <b>{{ stats.pass_count }}</b>
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-xs text-gray-500 uppercase tracking-wide">
              Average score
            </div>
            <div class="text-xl font-semibold">
              {{ stats.avg_score }}%
            </div>
            <div class="text-xs text-gray-500">
              Across all attempts
            </div>
          </div>

          <div class="space-y-1">
            <div class="text-xs text-gray-500 uppercase tracking-wide">
              Last activity
            </div>
            <div class="text-xs text-gray-700">
              Last attempt:<br>
              <span class="font-medium">
                {{ formatDate(stats.last_attempt) }}
              </span>
            </div>
            <div class="text-xs text-gray-700">
              Last pass:<br>
              <span class="font-medium">
                {{ formatDate(stats.last_pass) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section class="text-[11px] text-gray-500">
        <div class="font-semibold mb-1">
          Raw payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(stats, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
