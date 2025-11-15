<script setup>
const { get } = useApi()

const rows = ref([])
const loading = ref(true)
const err = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data = await get('/me/overdue-sops/')
    // accept either plain array or paginated { results: [...] }
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load')
  } finally {
    loading.value = false
  }
}

function formatDate (value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString()
}

function daysOverdue (value) {
  if (!value) return null
  const due = new Date(value)
  if (Number.isNaN(due.getTime())) return null
  const today = new Date()
  // strip time
  today.setHours(0, 0, 0, 0)
  due.setHours(0, 0, 0, 0)
  const diffMs = today - due
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  return diffDays > 0 ? diffDays : 0
}

// Decide where “Start training” sends the user
function startTrainingLink (item) {
  // If backend gave us a specific module, go straight there
  if (item.module_id) {
    return `/modules/${item.module_id}`
  }

  // Otherwise, fall back to the modules list filtered by skill/SOP
  const query = {}
  if (item.skill) query.skill = String(item.skill)
  if (item.sop) query.sop = String(item.sop)

  return { path: '/modules', query }
}

// decorate rows with derived values & sort
const decorated = computed(() =>
  rows.value
    .map(r => {
      const due = r.due_at || r.due_date
      const d = daysOverdue(due)
      return {
        ...r,
        _dueRaw: due,
        _daysOverdue: d,
      }
    })
    .sort((a, b) => {
      const ad = a._daysOverdue ?? 0
      const bd = b._daysOverdue ?? 0
      if (ad !== bd) return bd - ad
      const at = a._dueRaw ? new Date(a._dueRaw).getTime() : 0
      const bt = b._dueRaw ? new Date(b._dueRaw).getTime() : 0
      return at - bt
    })
)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <h1 class="text-2xl font-bold">
        My Overdue Training
      </h1>
      <button
        type="button"
        class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <p class="text-sm text-gray-600">
      These are skills or SOP-related requirements that have passed their due date or require re-certification.
    </p>

    <div v-if="loading" class="text-gray-500">
      Loading…
    </div>

    <div v-else-if="err" class="text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="decorated.length === 0" class="text-sm text-emerald-700">
        ✅ You have no overdue training requirements. Nice work!
      </div>

      <div
        v-else
        class="space-y-2"
      >
        <div
          v-for="item in decorated"
          :key="item.id"
          class="bg-white border rounded p-3 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">
              {{ item.skill_name || 'Unspecified skill' }}
            </div>
            <div class="text-xs text-gray-600 mt-0.5">
              Reason: {{ item.reason || 'Not specified' }}
            </div>

            <div
              v-if="item.meta"
              class="text-xs text-gray-500 mt-0.5 break-all"
            >
              Meta:
              {{
                typeof item.meta === 'string'
                  ? item.meta
                  : JSON.stringify(item.meta)
              }}
            </div>

            <div
              v-if="item.module_title"
              class="text-xs text-emerald-700 mt-0.5"
            >
              Module: {{ item.module_title }}
            </div>
          </div>

          <div class="text-xs text-right min-w-[8rem] space-y-1">
            <div>
              <span class="font-semibold">Due date:</span>
              <span>
                {{ formatDate(item._dueRaw) }}
              </span>
            </div>
            <div v-if="item._daysOverdue && item._daysOverdue > 0">
              <span class="inline-flex items-center rounded-full bg-red-100 text-red-700 px-2 py-0.5">
                {{ item._daysOverdue }}
                day<span v-if="item._daysOverdue !== 1">s</span> overdue
              </span>
            </div>
          </div>

          <div class="min-w-[9rem] flex justify-end">
            <NuxtLink
              :to="startTrainingLink(item)"
              class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
            >
              Start training
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
