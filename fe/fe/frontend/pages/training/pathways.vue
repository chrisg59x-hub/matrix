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

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/me/training-pathways/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load training pathways')
  } finally {
    loading.value = false
  }
}

function statusLabel (p: Pathway) {
  if (p.total_items === 0) return 'No modules attached yet'
  if (p.completed_items === 0) return 'Not started'
  if (p.completed_items >= p.total_items) return 'Completed'
  return 'In progress'
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          My Training Pathways
        </h1>
        <p class="text-sm text-gray-600">
          Structured training routes for your role, showing how far you are through each path.
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
      Loading training pathways…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No training pathways are assigned to you yet.
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="p in rows"
          :key="p.id"
          class="bg-white border rounded p-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">
              {{ p.name }}
            </div>
            <div
              v-if="p.description"
              class="text-xs text-gray-600 mt-0.5 line-clamp-2"
            >
              {{ p.description }}
            </div>

            <div class="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-600">
              <span class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5">
                {{ p.completed_items }} / {{ p.total_items || 0 }} modules completed
              </span>
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5"
                :class="p.percent_complete >= 100 ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'"
              >
                {{ p.percent_complete }}% complete
              </span>
              <span class="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5">
                {{ statusLabel(p) }}
              </span>
            </div>

            <!-- simple progress bar -->
            <div class="mt-2 w-full max-w-md">
              <div class="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                <div
                  class="h-2 rounded-full bg-emerald-500 transition-all"
                  :style="{ width: `${Math.min(100, Math.max(0, p.percent_complete))}%` }"
                />
              </div>
            </div>
          </div>

          <div class="flex gap-2 justify-end">
            <NuxtLink
              :to="`/training/pathways/${p.id}`"
              class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
            >
              View pathway
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
