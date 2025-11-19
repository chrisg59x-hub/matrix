<!-- frontend/pages/me/badges.vue -->
<script setup lang="ts">
const { get } = useApi()

type BadgeCore = {
  id: number
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

type UserBadgeRow = {
  id: number
  badge: BadgeCore
  awarded_at: string
  meta?: any
}

const loading = ref(true)
const err = ref<string | null>(null)
const rows = ref<UserBadgeRow[]>([])

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  rows.value = []

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
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleDateString()
}

function shortMeta (meta: any) {
  if (meta == null) return null
  if (typeof meta === 'string') return meta
  try {
    const s = JSON.stringify(meta)
    return s.length > 120 ? s.slice(0, 117) + '…' : s
  } catch {
    return String(meta)
  }
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <header class="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          My badges
        </h1>
        <p class="text-sm text-gray-600">
          Achievements and awards you’ve earned through training, XP, and supervisor sign-offs.
        </p>
      </div>

      <div class="flex items-center gap-2">
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
        You haven’t earned any badges yet. Complete training and gain XP to start unlocking them.
      </div>

      <div
        v-else
        class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        <article
          v-for="row in rows"
          :key="row.id"
          class="bg-white rounded-xl shadow-sm border p-4 flex flex-col gap-2"
        >
          <div class="flex items-start gap-3">
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center bg-emerald-50 text-emerald-700 text-xl"
            >
              <!-- If you later store an icon name, you can render it here -->
              <span v-if="row.badge.icon" class="i-lucide-award" />
              <span v-else class="i-lucide-award" />
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h2 class="font-semibold truncate">
                  {{ row.badge.name }}
                </h2>
                <span
                  v-if="row.badge.code"
                  class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] bg-gray-100 text-gray-600"
                >
                  {{ row.badge.code }}
                </span>
              </div>

              <p
                v-if="row.badge.description"
                class="text-xs text-gray-600 mt-0.5 line-clamp-3"
              >
                {{ row.badge.description }}
              </p>
            </div>
          </div>

          <div class="text-[11px] text-gray-600 space-y-0.5 mt-1">
            <div>
              <span class="font-semibold">Awarded:</span>
              <span class="ml-1">{{ formatDate(row.awarded_at) }}</span>
            </div>

            <div v-if="row.badge.skill_name">
              <span class="font-semibold">Skill:</span>
              <span class="ml-1">{{ row.badge.skill_name }}</span>
            </div>

            <div v-if="row.badge.team_name || row.badge.department_name">
              <span class="font-semibold">Team/Dept:</span>
              <span class="ml-1">
                {{ row.badge.team_name || '—' }}
                <span v-if="row.badge.department_name">
                  ({{ row.badge.department_name }})
                </span>
              </span>
            </div>

            <div v-if="row.badge.rule_type">
              <span class="font-semibold">Rule:</span>
              <span class="ml-1">
                {{ row.badge.rule_type }}
                <span v-if="row.badge.value != null">
                  – target {{ row.badge.value }}
                </span>
              </span>
            </div>

            <div v-if="shortMeta(row.meta)" class="text-[10px] text-gray-500">
              Meta: {{ shortMeta(row.meta) }}
            </div>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
