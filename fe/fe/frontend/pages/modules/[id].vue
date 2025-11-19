<!-- frontend/pages/modules/[id].vue -->
<script setup>
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const moduleId = computed(() => route.params.id)

const loading = ref(true)
const err = ref(null)
const item = ref(null)
const starting = ref(false)

onMounted(load)

async function load () {
  if (!moduleId.value) return
  loading.value = true
  err.value = null
  try {
    const data = await get(`/modules/${moduleId.value}/`)
    item.value = data
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load module')
  } finally {
    loading.value = false
  }
}

function difficultyLabel () {
  if (!item.value) return null
  return item.value.difficulty || item.value.level || item.value.level_label || null
}

function durationLabel () {
  if (!item.value) return null
  const n = item.value.estimated_minutes ?? item.value.duration_minutes ?? null
  if (!n || Number.isNaN(Number(n))) return null
  return `${n} min`
}

function xpLabel () {
  if (!item.value) return null
  const xp = item.value.xp_reward ?? item.value.xp ?? null
  if (!xp || Number.isNaN(Number(xp))) return null
  return `${xp} XP`
}

const prerequisites = computed(() => {
  if (!item.value) return []
  // try various shapes: array of objects, array of IDs, single object
  const raw = item.value.prerequisites || item.value.prerequisite_modules || []
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object') return [raw]
  return []
})

const nextModules = computed(() => {
  if (!item.value) return []
  const raw = item.value.next_modules || item.value.next_module || []
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object') return [raw]
  return []
})

async function startTraining () {
  if (!moduleId.value) return
  starting.value = true
  err.value = null
  try {
    const data = await post(`/modules/${moduleId.value}/start/`, {})
    const attemptId = data.attempt_id || data.id
    if (!attemptId) {
      throw new Error('Module start did not return attempt_id')
    }
    await router.push(`/modules/${moduleId.value}/attempt/${attemptId}`)
  } catch (e) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to start module')
  } finally {
    starting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          {{ item?.title || item?.name || 'Training Module' }}
        </h1>
        <p class="text-xs text-gray-500">
          Module ID: {{ moduleId }}
        </p>
      </div>

      <div class="flex flex-col items-end gap-2">
        <button
          type="button"
          class="px-4 py-2 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60"
          :disabled="starting || loading"
          @click="startTraining"
        >
          <span v-if="starting">Starting…</span>
          <span v-else>Start training</span>
        </button>

        <NuxtLink
          to="/modules"
          class="text-xs text-gray-600 hover:underline"
        >
          ← Back to modules
        </NuxtLink>
      </div>
    </div>

    <div v-if="loading" class="text-gray-500">
      Loading module details…
    </div>

    <div v-else-if="err" class="text-red-600 break-all text-sm">
      {{ err }}
    </div>

    <div v-else-if="!item" class="text-sm text-gray-600">
      Module not found.
    </div>

    <div v-else class="space-y-6">
      <!-- Summary chips -->
      <div class="flex flex-wrap gap-2 text-[11px] text-gray-700">
        <span
          v-if="difficultyLabel()"
          class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
        >
          Difficulty: {{ difficultyLabel() }}
        </span>
        <span
          v-if="durationLabel()"
          class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
        >
          {{ durationLabel() }}
        </span>
        <span
          v-if="xpLabel()"
          class="inline-flex items-center rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5"
        >
          {{ xpLabel() }}
        </span>
        <span
          v-if="item?.max_attempts"
          class="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5"
        >
          Max attempts: {{ item.max_attempts }}
        </span>
        <span
          v-if="item?.due_date || item?.due_at"
          class="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5"
        >
          Due: {{
            new Date(item.due_date || item.due_at).toLocaleDateString()
          }}
        </span>
      </div>

      <!-- Description -->
      <section>
        <h2 class="text-sm font-semibold text-gray-800 mb-1">
          Description
        </h2>
        <p class="text-sm text-gray-700 whitespace-pre-line">
          {{ item.description || 'No description provided.' }}
        </p>
      </section>

      <!-- Linked skills / SOPs (if present on serializer) -->
      <section v-if="item.skills || item.skill_names || item.sops || item.sop_titles">
        <h2 class="text-sm font-semibold text-gray-800 mb-1">
          Related skills & SOPs
        </h2>
        <div class="flex flex-wrap gap-2 text-[11px]">
          <template v-if="Array.isArray(item.skill_names)">
            <span
              v-for="s in item.skill_names"
              :key="`skill-${s}`"
              class="inline-flex items-center rounded-full bg-blue-50 text-blue-700 px-2 py-0.5"
            >
              {{ s }}
            </span>
          </template>
          <template v-else-if="Array.isArray(item.skills)">
            <span
              v-for="s in item.skills"
              :key="s.id || s"
              class="inline-flex items-center rounded-full bg-blue-50 text-blue-700 px-2 py-0.5"
            >
              {{ s.name || s.title || s.code || s }}
            </span>
          </template>

          <template v-if="Array.isArray(item.sop_titles)">
            <span
              v-for="t in item.sop_titles"
              :key="`sop-${t}`"
              class="inline-flex items-center rounded-full bg-purple-50 text-purple-700 px-2 py-0.5"
            >
              SOP: {{ t }}
            </span>
          </template>
          <template v-else-if="Array.isArray(item.sops)">
            <span
              v-for="s in item.sops"
              :key="s.id || s"
              class="inline-flex items-center rounded-full bg-purple-50 text-purple-700 px-2 py-0.5"
            >
              SOP: {{ s.title || s.name || s.code || s }}
            </span>
          </template>
        </div>
      </section>

      <!-- Simple module chain view -->
      <section class="grid gap-4 md:grid-cols-2">
        <div>
          <h2 class="text-sm font-semibold text-gray-800 mb-1">
            Prerequisite modules
          </h2>
          <div v-if="!prerequisites.length" class="text-xs text-gray-500">
            None defined.
          </div>
          <ul v-else class="space-y-1 text-sm">
            <li
              v-for="p in prerequisites"
              :key="p.id || p"
              class="flex items-center justify-between gap-2"
            >
              <span class="truncate">
                {{ p.title || p.name || p.code || p }}
              </span>
              <NuxtLink
                v-if="p.id"
                :to="`/modules/${p.id}`"
                class="text-xs text-emerald-700 hover:underline"
              >
                View
              </NuxtLink>
            </li>
          </ul>
        </div>

        <div>
          <h2 class="text-sm font-semibold text-gray-800 mb-1">
            Suggested next modules
          </h2>
          <div v-if="!nextModules.length" class="text-xs text-gray-500">
            None defined.
          </div>
          <ul v-else class="space-y-1 text-sm">
            <li
              v-for="n in nextModules"
              :key="n.id || n"
              class="flex items-center justify-between gap-2"
            >
              <span class="truncate">
                {{ n.title || n.name || n.code || n }}
              </span>
              <NuxtLink
                v-if="n.id"
                :to="`/modules/${n.id}`"
                class="text-xs text-emerald-700 hover:underline"
              >
                View
              </NuxtLink>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </div>
</template>
