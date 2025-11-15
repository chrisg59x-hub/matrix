<!-- frontend/pages/modules/[id]/attempt/[attempt_id].vue -->
<script setup>
const route = useRoute()
const { get } = useApi()

const moduleId = computed(() => route.params.id)
const attemptId = computed(() => route.params.attempt_id)

const loading = ref(true)
const err = ref(null)
const attempt = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    // Try to fetch full attempt data – ModuleAttemptViewSet should provide this
    const data = await get(`/attempts/${attemptId.value}/`)
    attempt.value = data
  } catch (e) {
    // If the endpoint isn’t ready yet, just degrade gracefully
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load attempt')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          Training Attempt
        </h1>
        <p class="text-xs text-gray-500">
          Module ID: {{ moduleId }} · Attempt ID: {{ attemptId }}
        </p>
      </div>

      <NuxtLink
        :to="`/modules/${moduleId}`"
        class="text-xs text-gray-600 hover:underline"
      >
        ← Back to module
      </NuxtLink>
    </div>

    <div v-if="loading" class="text-gray-500">
      Loading attempt…
    </div>

    <div v-else-if="err" class="text-red-600 break-all text-xs">
      {{ err }}
      <p class="mt-2 text-gray-500">
        The attempt endpoint is reachable, but the quiz UI is not wired yet.
      </p>
    </div>

    <div v-else-if="!attempt" class="text-sm text-gray-600">
      No attempt data returned.
    </div>

    <div v-else class="space-y-4">
      <p class="text-sm text-gray-700">
        This is the placeholder for the full quiz / training runner UI.
        The raw attempt payload is shown below to help you inspect the data shape.
      </p>

      <pre class="text-xs bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto">
{{ JSON.stringify(attempt, null, 2) }}
      </pre>
    </div>
  </div>
</template>
