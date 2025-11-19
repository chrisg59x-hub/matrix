<script setup>
const { get } = useApi()

const loading = ref(true)
const error = ref(null)
const data = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  error.value = null
  try {
    data.value = await get('/me/dashboard/')
  } catch (e) {
    error.value = e && e.data
      ? JSON.stringify(e.data)
      : (e && e.message ? e.message : 'Failed to load your dashboard')
  } finally {
    loading.value = false
  }
}

const passRate = computed(() => {
  if (!data.value) return 0
  if (!data.value.attempts_total) return 0
  return Math.round((data.value.attempts_passed / data.value.attempts_total) * 100)
})

function formatDate (val) {
  if (!val) return '—'
  try {
    const d = new Date(val)
    return d.toLocaleString()
  } catch {
    return String(val)
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        My training dashboard
      </h1>
      <p class="text-sm text-gray-600">
        Overview of your XP, quiz performance, and overdue training.
      </p>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading your dashboard…
    </div>

    <div
      v-else-if="error"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ error }}
    </div>

    <div v-else-if="data" class="space-y-4">
      <!-- XP & Level -->
      <section class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Overall XP
          </div>
          <div class="text-2xl font-semibold">
            {{ data.overall_xp }}
          </div>
          <div class="text-xs text-gray-500">
            Towards level {{ data.next_level }} ({{ data.xp_to_next }} XP to go)
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Level
          </div>
          <div class="text-2xl font-semibold">
            {{ data.overall_level }}
          </div>
          <div class="text-xs text-gray-500">
            Next level: {{ data.next_level }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Average score
          </div>
          <div class="text-2xl font-semibold">
            {{ data.avg_score }}%
          </div>
          <div class="text-xs text-gray-500">
            Across all attempts
          </div>
        </div>
      </section>

      <!-- Attempts -->
      <section class="grid gap-4 sm:grid-cols-3">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Attempts
          </div>
          <div class="text-2xl font-semibold">
            {{ data.attempts_total }}
          </div>
          <div class="text-xs text-gray-500">
            Last 30 days: {{ data.attempts_last_30_days }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Passed
          </div>
          <div class="text-2xl font-semibold">
            {{ data.attempts_passed }}
          </div>
          <div class="text-xs text-gray-500">
            Pass rate: {{ passRate }}%
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Activity (30 days)
          </div>
          <div class="text-2xl font-semibold">
            {{ data.attempts_last_30_days }}
          </div>
          <div class="text-xs text-gray-500">
            Attempts in the last 30 days
          </div>
        </div>
      </section>

      <!-- Overdue recert requirements -->
      <section class="space-y-2">
        <h2 class="text-sm font-semibold text-gray-800">
          Overdue training
        </h2>

        <div
          v-if="!data.overdue_recerts || !data.overdue_recerts.length"
          class="p-3 rounded bg-emerald-50 text-xs text-emerald-800"
        >
          🎉 You have no overdue recertification requirements.
        </div>

        <div
          v-else
          class="space-y-2"
        >
          <div
            v-for="item in data.overdue_recerts"
            :key="item.id"
            class="bg-white rounded-xl shadow p-3 text-xs space-y-1"
          >
            <div class="font-semibold text-gray-900">
              {{ item.skill_name || item.sop_title || 'Recert requirement' }}
            </div>
            <div class="text-gray-600">
              Reason:
              <span class="font-medium">{{ item.reason || 'expiry' }}</span>
            </div>
            <div class="text-gray-600">
              Due:
              <span class="font-medium">
                {{ item.due_date || formatDate(item.due_at) }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- Debug payload -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw dashboard payload (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(data, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
