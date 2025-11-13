<script setup lang="ts">
const { get } = useApi()

type Row = Record<string, any>

const rows = ref<Row[]>([])
const sopViewMap = ref<Record<string, any>>({})
const loading = ref(true)
const err = ref<string | null>(null)

onMounted(load)

async function load() {
  loading.value = true
  err.value = null
  try {
    // Overdue SOPs
    const data: any = await get('/me/overdue-sops/')
    rows.value = Array.isArray(data) ? data : (data.results || [])

    // Views (for progress)
    const views: any = await get('/me/sop-views/')
    const list = Array.isArray(views) ? views : (views.results || [])
    const map: Record<string, any> = {}
    for (const v of list) {
      if (v.sop) {
        map[String(v.sop)] = v
      }
    }
    sopViewMap.value = map
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load overdue SOPs')
  } finally {
    loading.value = false
  }
}

function getView(row: Row) {
  return sopViewMap.value[String(row.id)] || null
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">My Overdue Training</h1>
      <p class="mt-1 text-sm text-slate-600">
        SOPs that are currently overdue for you, based on recertification rules.
      </p>
    </div>

    <div v-if="loading" class="text-gray-500">Loading…</div>
    <div v-else-if="err" class="text-red-600 break-all">{{ err }}</div>

    <div v-else-if="rows.length === 0" class="text-sm text-emerald-700">
      🎉 You have no overdue SOPs right now.
    </div>

    <ul v-else class="space-y-2">
      <li
        v-for="r in rows"
        :key="r.id"
        class="border rounded p-3 flex items-center gap-4"
      >
        <div class="flex-1 min-w-0 space-y-1">
          <div class="flex items-center gap-2">
            <div class="font-medium truncate">
              {{ r.title || r.name || r.code || r.id }}
            </div>
            <span
              class="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700"
            >
              Overdue
            </span>
          </div>

          <div class="text-xs text-gray-600 truncate">
            {{ r.description || r.summary || '' }}
          </div>

          <!-- Progress for this SOP -->
          <div class="mt-1 text-xs flex flex-wrap gap-2 items-center">
            <span
              v-if="getView(r)?.completed"
              class="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700"
            >
              ✓ Completed (but still marked overdue)
            </span>
            <span
              v-else-if="getView(r)"
              class="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 font-medium text-amber-700"
            >
              In progress ·
              {{ Math.round(((getView(r).progress || 0) * 100)) }}%
            </span>
            <span
              v-else
              class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-slate-500"
            >
              Not started
            </span>
          </div>
        </div>

        <div class="flex flex-col items-end gap-2">
          <NuxtLink
            :to="`/sops/${r.id}`"
            class="inline-flex items-center rounded bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
          >
            View SOP
          </NuxtLink>

          <NuxtLink
            to="/sops"
            class="text-[11px] text-slate-500 hover:text-slate-700 underline"
          >
            Back to all SOPs
          </NuxtLink>
        </div>
      </li>
    </ul>
  </div>
</template>
