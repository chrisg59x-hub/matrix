<script setup lang="ts">
const { get } = useApi()

type Badge = {
  id: string
  code: string
  name: string
  description?: string | null
  rule_type: string
  value: number
  skill_name?: string | null
  team_name?: string | null
  department_name?: string | null
  icon?: string | null
}

type UserBadge = {
  id: string
  badge: Badge
  awarded_at: string
  meta?: any
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<UserBadge[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data: any = await get('/me/badges/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load badges')
  } finally {
    loading.value = false
  }
}

function formatDate (value: string | null | undefined) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString() + ' ' +
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function prettyRule (rule: string) {
  const map: Record<string, string> = {
    overall_xp_at_least: 'Overall XP at least',
    skill_xp_at_least: 'Skill XP at least',
    signoffs_at_least: 'Supervisor sign-offs',
    team_total_xp_at_least: 'Team total XP at least',
    department_total_xp_at_least: 'Department total XP at least',
    team_member_count_with_xp_at_least: 'Team members with XP at least',
  }
  return map[rule] || rule
}

function formatMeta (meta: any): string | null {
  if (meta == null) return null
  if (typeof meta === 'string') return meta
  try {
    return JSON.stringify(meta)
  } catch {
    return String(meta)
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        My Badges
      </h1>
      <p class="text-sm text-gray-600">
        Achievements and milestones you’ve earned from training and XP.
      </p>
    </header>

    <div class="flex justify-end">
      <button
        type="button"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <!-- States -->
    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading badges…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rows.length === 0" class="text-sm text-gray-600">
        You haven’t earned any badges yet. Keep completing training and gaining XP
        to unlock achievements.
      </div>

      <div v-else class="space-y-3">
        <div class="text-sm text-gray-600">
          You’ve earned
          <span class="font-semibold">{{ rows.length }}</span>
          badge<span v-if="rows.length !== 1">s</span>.
        </div>

        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="ub in rows"
            :key="ub.id"
            class="bg-white rounded-xl shadow-sm border p-3 flex flex-col gap-2"
          >
            <!-- Badge header -->
            <div class="flex items-start gap-2">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center">
                  <span class="i-lucide-award text-emerald-700 text-lg" />
                </div>
              </div>

              <div class="min-w-0">
                <div class="font-semibold truncate">
                  {{ ub.badge?.name || 'Badge' }}
                </div>
                <div class="text-[11px] text-gray-500 truncate">
                  Code: {{ ub.badge?.code }}
                </div>
              </div>
            </div>

            <!-- Rule / value -->
            <div class="text-xs text-gray-600">
              <div class="font-medium">
                {{ prettyRule(ub.badge?.rule_type || '') }}
              </div>
              <div v-if="ub.badge?.value != null">
                Threshold / value: <b>{{ ub.badge.value }}</b>
              </div>
            </div>

            <!-- Context (skill / team / department) -->
            <div class="text-[11px] text-gray-500 space-y-0.5">
              <div v-if="ub.badge?.skill_name">
                Skill: {{ ub.badge.skill_name }}
              </div>
              <div v-if="ub.badge?.team_name">
                Team: {{ ub.badge.team_name }}
              </div>
              <div v-if="ub.badge?.department_name">
                Department: {{ ub.badge.department_name }}
              </div>
            </div>

            <!-- Description -->
            <p
              v-if="ub.badge?.description"
              class="text-xs text-gray-700 line-clamp-3"
            >
              {{ ub.badge.description }}
            </p>

            <!-- Award info -->
            <div class="mt-auto pt-2 border-t text-[11px] text-gray-500 flex justify-between items-center">
              <span>
                Awarded:
                <span class="font-medium">
                  {{ formatDate(ub.awarded_at) }}
                </span>
              </span>
              <span v-if="formatMeta(ub.meta)" class="truncate max-w-[8rem]">
                Meta:
                {{ formatMeta(ub.meta) }}
              </span>
            </div>
          </article>
        </div>
      </div>
    </div>
  </div>
</template>
