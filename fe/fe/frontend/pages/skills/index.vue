<!-- frontend/pages/skills/index.vue -->
<script setup lang="ts">
const { get } = useApi()

type SkillRow = {
  id: string
  name: string
  risk_level: string
  valid_for_days: number
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<SkillRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/skills/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load skills')
  } finally {
    loading.value = false
  }
}

function riskLabel (risk: string) {
  if (!risk) return '—'
  const m = {
    low: 'Low',
    med: 'Medium',
    high: 'High',
  } as Record<string, string>
  return m[risk] || risk
}

function riskClass (risk: string) {
  switch (risk) {
    case 'low':
      return 'bg-emerald-50 text-emerald-700 border border-emerald-100'
    case 'high':
      return 'bg-red-50 text-red-700 border border-red-100'
    case 'med':
    default:
      return 'bg-amber-50 text-amber-700 border border-amber-100'
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-4">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Skills
        </h1>
        <p class="text-sm text-gray-600">
          Safety and competency skills with risk level and recertification period.
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
      Loading skills…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No skills found.
      </div>

      <div v-else class="overflow-x-auto bg-white border rounded-xl shadow-sm">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-3 py-2 text-left">
                Skill
              </th>
              <th class="px-3 py-2 text-left">
                Risk
              </th>
              <th class="px-3 py-2 text-right">
                Valid for
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="s in rows"
              :key="s.id"
              class="hover:bg-gray-50"
            >
              <td class="px-3 py-2">
                <div class="font-medium">
                  {{ s.name }}
                </div>
              </td>
              <td class="px-3 py-2">
                <span
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px]"
                  :class="riskClass(s.risk_level)"
                >
                  {{ riskLabel(s.risk_level) }}
                </span>
              </td>
              <td class="px-3 py-2 text-right">
                <span v-if="s.valid_for_days">
                  {{ s.valid_for_days }} day<span v-if="s.valid_for_days !== 1">s</span>
                </span>
                <span v-else>
                  —
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
