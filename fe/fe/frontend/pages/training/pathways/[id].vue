<script setup lang="ts">
const { get, post } = useApi()
const router = useRouter()
const route = useRoute()

type Item = {
  id: number
  required: boolean
  order: number
  notes?: string | null
  module?: {
    id: number
    title?: string | null
    skill?: number | null
    sop?: string | null
  } | null
}

type Pathway = {
  id: number
  name: string
  description?: string | null
  items: Item[]
}

const loading = ref(true)
const err = ref<string | null>(null)
const pathway = ref<Pathway | null>(null)
const startingId = ref<number | null>(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const id = route.params.id
    const data: any = await get(`/training-pathways/${id}/`)
    pathway.value = data
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load pathway')
  } finally {
    loading.value = false
  }
}

async function startModule (item: Item) {
  if (!item.module?.id) return
  startingId.value = item.module.id
  err.value = null
  try {
    const data: any = await post(`/modules/${item.module.id}/start/`, {})
    const attemptId = data.attempt_id || data.id
    if (!attemptId) throw new Error('Module start did not return attempt_id')
    await router.push(`/modules/${item.module.id}/attempt/${attemptId}`)
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to start module')
  } finally {
    startingId.value = null
  }
}
</script>

<template>
  <div class="space-y-4">
    <div v-if="loading" class="text-sm text-gray-500">
      Loading pathway…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else-if="pathway" class="space-y-4">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold">
            {{ pathway.name }}
          </h1>
          <p class="text-sm text-gray-600">
            {{ pathway.description || 'Training modules included in this pathway.' }}
          </p>
        </div>

        <NuxtLink
          to="/training/pathways"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        >
          Back to pathways
        </NuxtLink>
      </div>

      <div v-if="pathway.items.length === 0" class="text-sm text-gray-600">
        No modules are configured for this pathway yet.
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="item in pathway.items"
          :key="item.id"
          class="bg-white border rounded p-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">
              {{ item.module?.title || 'Unassigned module' }}
            </div>
            <div class="mt-0.5 text-xs text-gray-600">
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
                :class="item.required ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-700'"
              >
                {{ item.required ? 'Required' : 'Optional' }}
              </span>
            </div>
            <div
              v-if="item.notes"
              class="mt-1 text-xs text-gray-500"
            >
              {{ item.notes }}
            </div>
          </div>

          <div class="flex gap-2 justify-end">
            <NuxtLink
              v-if="item.module?.id"
              :to="`/modules/${item.module.id}`"
              class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
            >
              View module
            </NuxtLink>
            <button
              v-if="item.module?.id"
              type="button"
              class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
              :disabled="startingId === item.module.id"
              @click="startModule(item)"
            >
              <span v-if="startingId === item.module.id">Starting…</span>
              <span v-else>Start training</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
