<!-- frontend/pages/manager/badges.vue -->
<script setup lang="ts">
const { get } = useApi()

type BadgeCore = {
  id: string
  code?: string | null
  name: string
  description?: string | null
  rule_type?: string | null
  value?: number | null
  skill_name?: string | null
  team_name?: string | null
  department_name?: string | null
  icon?: string | null
}

type BadgeRuleRow = {
  badge: BadgeCore
  holder_count: number
  sample_holders: string[]
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<BadgeRuleRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  rows.value = []

  try {
    const data: any = await get('/manager/badges/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load badge rules')
  } finally {
    loading.value = false
  }
}

function ruleLabel (row: BadgeRuleRow) {
  const b = row.badge
  if (!b.rule_type) return 'Custom rule'
  let base = b.rule_type.replace(/_/g, ' ')
  base = base.charAt(0).toUpperCase() + base.slice(1)
  if (b.value != null) {
    base += ` ≥ ${b.value}`
  }
  return base
}

function contextLabel (row: BadgeRuleRow) {
  const b = row.badge
  const bits: string[] = []
  if (b.skill_name) bits.push(`Skill: ${b.skill_name}`)
  if (b.team_name) bits.push(`Team: ${b.team_name}`)
  if (b.department_name) bits.push(`Dept: ${b.department_name}`)
  return bits.join(' · ')
}
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Badge rules
        </h1>
        <p class="text-sm text-gray-600">
          Overview of all badge rules in your organisation, who can earn them, and how many users hold each badge.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <NuxtLink
          to="/leaderboard"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        >
          View user leaderboard
        </NuxtLink>

        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </header>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading badge rules…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        No badges defined yet. Create badge rules in the admin or via the API to start awarding achievements.
      </div>

      <div
        v-else
        class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        <article
          v-for="row in rows"
          :key="row.badge.id"
          class="bg-white rounded-xl shadow-sm border p-4 flex flex-col gap-2"
        >
          <!-- Badge header -->
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-700">
              <!-- You can later switch this to row.badge.icon if you store e.g. lucide names -->
              <span class="i-lucide-award text-xl"></span>
            </div>

            <div class="flex-1 min-w-0">
              <h2 class="font-semibold truncate">
                {{ row.badge.name }}
              </h2>
              <p
                v-if="row.badge.description"
                class="text-xs text-gray-600 mt-0.5 line-clamp-3"
              >
                {{ row.badge.description }}
              </p>
            </div>
          </div>

          <!-- Rule & Context -->
          <div class="text-[11px] text-gray-600 space-y-0.5">
            <div v-if="row.badge.code">
              <span class="font-semibold">Code:</span>
              <span class="ml-1">{{ row.badge.code }}</span>
            </div>

            <div>
              <span class="font-semibold">Rule:</span>
              <span class="ml-1">{{ ruleLabel(row) }}</span>
            </div>

            <div v-if="contextLabel(row)">
              <span class="font-semibold">Context:</span>
              <span class="ml-1">{{ contextLabel(row) }}</span>
            </div>
          </div>

          <!-- Holders -->
          <div class="mt-2 text-[11px] text-gray-700 space-y-0.5">
            <div>
              <span class="font-semibold">Holders:</span>
              <span class="ml-1">
                {{ row.holder_count }}
              </span>
            </div>

            <div v-if="row.sample_holders && row.sample_holders.length">
              <span class="font-semibold">Examples:</span>
              <span class="ml-1">
                {{ row.sample_holders.join(', ') }}
              </span>
            </div>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
