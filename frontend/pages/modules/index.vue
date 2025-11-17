<!-- frontend/pages/modules/index.vue -->
<script setup>
const { get, post } = useApi()
const router = useRouter()
const route = useRoute()

// Query-driven filters
const onlyOverdue = computed(() => route.query.onlyOverdue === '1')
const skillFilter = computed(() =>
  route.query.skill ? Number(route.query.skill) : null
)

const loading = ref(true)
const err = ref(null)
const rows = ref([])

const search = ref('')
const onlyAvailable = ref(false)
const startingId = ref(null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  try {
    const data = await get('/modules/')
    rows.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load modules')
  } finally {
    loading.value = false
  }
}

function matchesSearch (m) {
  if (!search.value) return true
  const q = search.value.toLowerCase()
  const parts = [
    m.title,
    m.name,
    m.code,
    m.description
  ].filter(Boolean).join(' ').toLowerCase()
  return parts.includes(q)
}

function isAvailable (m) {
  // you can refine this later if backend has flags like is_available, archived, etc
  if (!onlyAvailable.value) return true
  if (m.archived === true) return false
  // treat everything else as available
  return true
}

// Filter by skill (from ?skill=ID). Tries a few common shapes.
function matchesSkill (m) {
  const id = skillFilter.value
  if (!id) return true

  // direct field
  if (m.skill_id && Number(m.skill_id) === id) return true

  // array of skills e.g. [{id,...}] or [{skill_id,...}] or [id, id, ...]
  if (Array.isArray(m.skills)) {
    if (m.skills.some(s => Number(s.id ?? s.skill_id ?? s) === id)) return true
  }

  // array of raw ids
  if (Array.isArray(m.skill_ids)) {
    if (m.skill_ids.some(sid => Number(sid) === id)) return true
  }

  return false
}

// Filter by overdue flag (?onlyOverdue=1)
function matchesOverdue (m) {
  if (!onlyOverdue.value) return true

  // Prefer backend flag if present
  if (typeof m.is_overdue !== 'undefined') {
    return !!m.is_overdue
  }

  // Fallback to client-side date check if fields are present
  const raw = m.due_date || m.due_at
  if (raw) {
    const d = new Date(raw)
    if (!Number.isNaN(d.getTime())) {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      d.setHours(0, 0, 0, 0)
      return d.getTime() <= today.getTime()
    }
  }

  // If we can't tell, don't automatically hide it.
  return true
}

// 🔹 Helper: nice label for due date (from backend due_date/due_at)
function moduleDueDate (m) {
  const raw = m.due_date || m.due_at
  if (!raw) return null
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString()
}

const filtered = computed(() =>
  rows.value
    .filter(matchesSearch)
    .filter(isAvailable)
    .filter(matchesSkill)
    .filter(matchesOverdue)
)

function difficultyLabel (m) {
  // try common fields, fall back gracefully
  return m.difficulty || m.level || m.level_label || null
}

function durationLabel (m) {
  const n = m.estimated_minutes ?? m.duration_minutes ?? null
  if (!n || Number.isNaN(Number(n))) return null
  return `${n} min`
}

function xpLabel (m) {
  const xp = m.xp_reward ?? m.xp ?? null
  if (!xp || Number.isNaN(Number(xp))) return null
  return `${xp} XP`
}

async function startModule (mod) {
  if (!mod?.id) return
  startingId.value = mod.id
  err.value = null
  try {
    const data = await post(`/modules/${mod.id}/start/`, {})
    const attemptId = data.attempt_id || data.id
    if (!attemptId) {
      throw new Error('Module start did not return attempt_id')
    }
    await router.push(`/modules/${mod.id}/attempt/${attemptId}`)
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to start module')
  } finally {
    startingId.value = null
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Training Modules
        </h1>
        <p class="text-sm text-gray-600">
          Browse available training modules. Start a module to begin a tracked attempt.
        </p>

        <!-- Small hint about active route filters -->
        <p
          v-if="onlyOverdue || skillFilter"
          class="mt-1 text-xs text-emerald-700"
        >
          Showing
          <span v-if="onlyOverdue">only overdue&nbsp;</span>
          <span v-if="skillFilter">modules linked to skill #{{ skillFilter }}</span>
        </p>
      </div>

      <div class="flex flex-col sm:flex-row gap-2 sm:items-center">
        <input
          v-model="search"
          type="search"
          class="border rounded px-3 py-1.5 text-sm min-w-[14rem]"
          placeholder="Search modules…"
        >
        <label class="flex items-center gap-2 text-xs text-gray-700">
          <input
            v-model="onlyAvailable"
            type="checkbox"
            class="rounded border-gray-300"
          >
          Show only available
        </label>
        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="load"
        >
          Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-gray-500">
      Loading modules…
    </div>

    <div v-else-if="err" class="text-red-600 break-all text-sm">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="filtered.length === 0" class="text-sm text-gray-600">
        No modules match your filters.
        <span v-if="onlyOverdue || skillFilter">
          Try clearing the filters or navigating from
          <NuxtLink to="/training/overdue" class="text-emerald-700 underline">
            My Overdue Training
          </NuxtLink>.
        </span>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="m in filtered"
          :key="m.id"
          class="bg-white border rounded p-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4"
        >
          <div class="flex-1 min-w-0">
            <div class="font-medium truncate">
              {{ m.title || m.name || m.code || 'Untitled module' }}
            </div>
            <div
              v-if="m.description"
              class="text-xs text-gray-600 line-clamp-2"
            >
              {{ m.description }}
            </div>

            <!-- Badge row: difficulty, duration, XP, due date, overdue -->
            <div class="mt-1 flex flex-wrap gap-2 text-[11px] text-gray-600">
              <span
                v-if="difficultyLabel(m)"
                class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
              >
                Difficulty: {{ difficultyLabel(m) }}
              </span>
              <span
                v-if="durationLabel(m)"
                class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
              >
                {{ durationLabel(m) }}
              </span>
              <span
                v-if="xpLabel(m)"
                class="inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5"
              >
                {{ xpLabel(m) }}
              </span>

              <!-- 🔹 New: due date badge -->
              <span
                v-if="moduleDueDate(m)"
                class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
              >
                Due: {{ moduleDueDate(m) }}
              </span>

              <!-- 🔹 New: Overdue pill -->
              <span
                v-if="m.is_overdue"
                class="inline-flex items-center rounded-full bg-red-100 text-red-700 px-2 py-0.5"
              >
                Overdue
              </span>
            </div>
          </div>

          <div class="flex gap-2 justify-end">
            <NuxtLink
              :to="`/modules/${m.id}`"
              class="px-3 py-1.5 text-xs rounded border border-gray-300 bg-white hover:bg-gray-50"
            >
              View details
            </NuxtLink>
            <button
              type="button"
              class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
              :disabled="startingId === m.id"
              @click="startModule(m)"
            >
              <span v-if="startingId === m.id">Starting…</span>
              <span v-else>Start training</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
