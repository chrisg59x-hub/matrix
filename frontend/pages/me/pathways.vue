<!-- frontend/pages/me/pathways.vue -->
<script setup lang="ts">
const { get } = useApi()

type Pathway = {
  id: number
  name: string
  description?: string | null
  total_items: number
  completed_items: number
  percent_complete: number
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<Pathway[]>([])

// simple status filter
const statusFilter = ref<'all' | 'inprogress' | 'complete'>('all')

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/me/training-pathways/')
    // endpoint returns a plain array of objects
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load training pathways')
  } finally {
    loading.value = false
  }
}

const filtered = computed<Pathway[]>(() => {
  return rows.value.filter(p => {
    if (statusFilter.value === 'all') return true
    const complete = (p.completed_items || 0) >= (p.total_items || 0) && p.total_items > 0
    if (statusFilter.value === 'complete') return complete
    if (statusFilter.value === 'inprogress') return !complete
    return true
  })
})

function statusLabel (p: Pathway) {
  if (!p.total_items || p.total_items === 0) return 'Not configured'
  const complete = (p.completed_items || 0) >= p.total_items
  return complete ? 'Completed' : 'In progress'
}

function statusBadgeClass (p: Pathway) {
  if (!p.total_items || p.total_items === 0) {
    return 'bg-gray-100 text-gray-600'
  }
  const complete = (p.completed_items || 0) >= p.total_items
  return complete
    ? 'bg-emerald-100 text-emerald-700'
    : 'bg-blue-100 text-blue-700'
}

function safePercent (p: Pathway) {
  const n = Number(p.percent_complete || 0)
  if (Number.isNaN(n) || n < 0) return 0
  if (n > 100) return 100
  return Math.round(n)
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          My Training Pathways
        </h1>
        <p class="text-sm text-gray-600">
          High-level view of your training routes – each pathway groups modules and skills
          for a role, department, or level.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <select
          v-model="statusFilter"
          class="border rounded px-2 py-1.5 text-xs"
        >
          <option value="all">
            All pathways
          </option>
          <option value="inprogress">
            In progress
          </option>
          <option value="complete">
            Completed
          </option>
        </select>

        <button
          type="button"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </header>

    <!-- Loading / error states -->
    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading pathways…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="filtered.length === 0"
      class="p-4 rounded bg-white border text-sm text-gray-600"
    >
      <p v-if="rows.length === 0">
        No training pathways have been set up for your organisation yet.
      </p>
      <p v-else>
        No pathways match your current filter.
        Try changing the status filter above.
      </p>
    </div>

    <!-- Pathways list -->
    <div v-else class="space-y-4">
      <div
        v-for="p in filtered"
        :key="p.id"
        class="bg-white border rounded-xl shadow-sm p-4 flex flex-col gap-3 sm:flex-row sm:items-center"
      >
        <!-- Left: name + description + status -->
        <div class="flex-1 min-w-0 space-y-1">
          <div class="flex items-center gap-2">
            <h2 class="font-semibold truncate">
              {{ p.name }}
            </h2>
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
              :class="statusBadgeClass(p)"
            >
              {{ statusLabel(p) }}
            </span>
          </div>

          <p
            v-if="p.description"
            class="text-xs text-gray-600 line-clamp-2"
          >
            {{ p.description }}
          </p>

          <div class="text-[11px] text-gray-500">
            {{ p.completed_items }} / {{ p.total_items }} items completed
          </div>
        </div>

        <!-- Right: progress bar + percentage -->
        <div class="w-full sm:w-64 space-y-1">
          <div class="flex items-center justify-between text-xs text-gray-600">
            <span>Progress</span>
            <span class="font-semibold">
              {{ safePercent(p) }}%
            </span>
          </div>
          <div class="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-emerald-500 rounded-full transition-all"
              :style="{ width: `${safePercent(p)}%` }"
            />
          </div>

          <div class="flex justify-end gap-2 pt-1">
            <NuxtLink
              :to="`/me/pathways/${p.id}`"
              class="inline-flex items-center px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
            >
              View pathway
            </NuxtLink>

            <NuxtLink
              to="/modules"
              class="inline-flex items-center px-3 py-1.5 text-xs rounded border bg-white text-gray-700 hover:bg-gray-50"
            >
              All modules
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <!-- (Optional) raw debug payload – handy while we’re still wiring things up -->
    <section class="space-y-1 text-[10px] text-gray-500">
      <div class="font-semibold">
        Raw pathways payload (debug)
      </div>
      <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(rows, null, 2) }}
      </pre>
    </section>
  </div>
</template>
