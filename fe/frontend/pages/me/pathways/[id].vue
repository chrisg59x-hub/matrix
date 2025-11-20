<!-- frontend/pages/me/pathways/[id].vue -->
<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

// --- Types matching your serializers ---------------------------------------

type ModuleMini = {
  id: number
  title?: string | null
  skill?: number | null
}

type PathwayItem = {
  id: number
  required: boolean
  order: number
  notes?: string | null
  module: ModuleMini | null
  skill?: number | null
  sop_label?: string | null
}

type PathwayDetail = {
  id: number
  name: string
  description?: string | null
  job_role_label?: string | null
  department_label?: string | null
  level_label?: string | null
  active: boolean
  items: PathwayItem[]
}

type Attempt = {
  id: string
  module: {
    id: number
    title?: string | null
    skill?: number | null
    sop?: string | null
  } | null
  created_at: string
  completed_at: string | null
  score: number
  passed: boolean
}

type ItemStatus = 'not_started' | 'inprogress' | 'passed' | 'failed'

// --- State ------------------------------------------------------------------

const loading = ref(true)
const err = ref<string | null>(null)
const pathway = ref<PathwayDetail | null>(null)
const startingRecommended = ref(false)
const startError = ref<string | null>(null)

// latest attempt per module_id
const attemptByModuleId = ref<Record<number, Attempt | undefined>>({})

// --- Load data --------------------------------------------------------------

onMounted(load)

async function load () {
  loading.value = true
  err.value = null
  pathway.value = null
  attemptByModuleId.value = {}

  try {
    const id = route.params.id

    const [pData, attemptsData]: [any, any] = await Promise.all([
      get(`/training-pathways/${id}/`),
      get('/me/module-attempts/'),
    ])

    pathway.value = pData

    const attempts: Attempt[] = Array.isArray(attemptsData)
      ? attemptsData
      : (attemptsData.results || [])

    // rows already ordered newest-first; keep first per module as "latest"
    const map: Record<number, Attempt> = {}
    for (const a of attempts) {
      const mid = a.module?.id
      if (!mid) continue
      if (!map[mid]) {
        map[mid] = a
      }
    }
    attemptByModuleId.value = map
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load pathway')
  } finally {
    loading.value = false
  }
}

// --- Derived data -----------------------------------------------------------

const enrichedItems = computed(() => {
  const p = pathway.value
  if (!p?.items) return []

  return p.items
    .slice()
    .sort((a, b) => (a.order || 0) - (b.order || 0))
    .map(item => {
      const moduleId = item.module?.id ?? null
      const attempt = moduleId ? attemptByModuleId.value[moduleId] : undefined

      let status: ItemStatus = 'not_started'
      if (attempt) {
        if (!attempt.completed_at) {
          status = 'inprogress'
        } else {
          status = attempt.passed ? 'passed' : 'failed'
        }
      }

      return {
        ...item,
        _status: status as ItemStatus,
        _attempt: attempt,
      }
    })
})

const summary = computed(() => {
  const items = enrichedItems.value
  const required = items.filter(i => i.required && i.module?.id)
  const total = required.length
  const passed = required.filter(i => i._status === 'passed').length
  const inprogress = required.filter(i => i._status === 'inprogress').length
  const failed = required.filter(i => i._status === 'failed').length

  const percent = total > 0 ? Math.round((passed / total) * 100) : 0

  return { total, passed, inprogress, failed, percent }
})

/**
 * NEW: recommended next item
 * First required item that:
 *  - has a module
 *  - is not yet passed
 * Ordered by "order" already via enrichedItems.
 */
const recommendedItem = computed(() =>
  enrichedItems.value.find(
    (i: any) => i.required && i.module?.id && i._status !== 'passed',
  ) || null,
)

// --- Helpers ----------------------------------------------------------------

function statusLabel (status: ItemStatus) {
  if (status === 'not_started') return 'Not started'
  if (status === 'inprogress') return 'In progress'
  if (status === 'passed') return 'Passed'
  if (status === 'failed') return 'Failed'
  return 'Unknown'
}

function statusBadgeClass (status: ItemStatus) {
  switch (status) {
    case 'passed':
      return 'bg-emerald-100 text-emerald-700'
    case 'inprogress':
      return 'bg-blue-100 text-blue-700'
    case 'failed':
      return 'bg-red-100 text-red-700'
    case 'not_started':
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function safePercent (n: number) {
  if (Number.isNaN(n) || n < 0) return 0
  if (n > 100) return 100
  return n
}

function goBack () {
  router.push('/me/pathways')
}

function goToModule (item: any) {
  const moduleId = item?.module?.id
  if (!moduleId) return
  router.push(`/modules/${moduleId}`)
}

async function goToRecommended () {
  if (!recommendedItem.value) return
  const moduleId = recommendedItem.value.module?.id
  if (!moduleId) return

  startingRecommended.value = true
  startError.value = null

  try {
    // Call the quiz engine "start attempt" endpoint
    const data: any = await post(`/modules/${moduleId}/attempt/start/`, {})

    const attemptId = data?.attempt_id
    const returnedModuleId = data?.module_id || moduleId

    if (!attemptId) {
      throw new Error('No attempt_id returned from API')
    }

    // Jump straight into the attempt view
    await router.push(`/modules/${returnedModuleId}/attempt/${attemptId}`)
  } catch (e: any) {
    startError.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to start attempt')
  } finally {
    startingRecommended.value = false
  }
}

</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <header class="space-y-2">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h1 class="text-2xl font-bold">
            {{ pathway?.name || 'Training pathway' }}
          </h1>
          <p v-if="pathway?.description" class="text-sm text-gray-600">
            {{ pathway.description }}
          </p>
        </div>

        <button
          type="button"
          class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
          @click="goBack"
        >
          Back to pathways
        </button>
      </div>

      <div
        v-if="pathway"
        class="flex flex-wrap gap-2 text-[11px] text-gray-500"
      >
        <span v-if="pathway.job_role_label">
          Role: <b>{{ pathway.job_role_label }}</b>
        </span>
        <span v-if="pathway.department_label">
          Department: <b>{{ pathway.department_label }}</b>
        </span>
        <span v-if="pathway.level_label">
          Level: <b>{{ pathway.level_label }}</b>
        </span>
        <span v-if="!pathway.active" class="text-red-600">
          (Inactive pathway)
        </span>
      </div>
    </header>

    <!-- Loading / error -->
    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading pathway…
    </div>

    <div
      v-else-if="err"
      class="p-3 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
    >
      {{ err }}
    </div>

    <div v-else-if="pathway" class="space-y-6">
      <!-- NEW: Recommended next step card -->
      <section v-if="recommendedItem" class="bg-emerald-50 border border-emerald-100 rounded-xl p-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <div class="flex-1 min-w-0">
          <div class="text-xs font-semibold uppercase text-emerald-700 tracking-wide">
            Recommended next step
          </div>
          <div class="mt-1 font-semibold text-sm truncate">
            {{ recommendedItem.module?.title || 'Next required module' }}
          </div>
          <p v-if="recommendedItem.notes" class="mt-1 text-xs text-emerald-900 line-clamp-2">
            {{ recommendedItem.notes }}
          </p>
          <p v-else class="mt-1 text-xs text-emerald-900">
            This is the next required item that you haven’t passed yet.
          </p>
        </div>

        <div class="flex flex-col items-end gap-2 min-w-[10rem]">
          <span
            class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
            :class="statusBadgeClass(recommendedItem._status)"
          >
            {{ statusLabel(recommendedItem._status) }}
          </span>
          <button
            type="button"
            class="inline-flex items-center px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="startingRecommended"
            @click="goToRecommended"
            >
            <span v-if="startingRecommended">Starting…</span>
            <span v-else>Start next step</span>
            </button>
            <p
            v-if="startError"
            class="mt-1 text-[11px] text-red-600 text-right"
            >
            {{ startError }}
            </p>
        </div>
      </section>

      <!-- Summary cards -->
      <section class="grid gap-4 sm:grid-cols-4">
        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Required items
          </div>
          <div class="text-2xl font-semibold">
            {{ summary.total }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Passed
          </div>
          <div class="text-2xl font-semibold text-emerald-700">
            {{ summary.passed }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            In progress
          </div>
          <div class="text-2xl font-semibold text-blue-700">
            {{ summary.inprogress }}
          </div>
        </div>

        <div class="bg-white rounded-xl shadow p-4 space-y-1">
          <div class="text-xs text-gray-500 uppercase tracking-wide">
            Overall progress
          </div>
          <div class="text-2xl font-semibold">
            {{ safePercent(summary.percent) }}%
          </div>
        </div>
      </section>

      <!-- Progress bar -->
      <section class="bg-white rounded-xl shadow p-4 space-y-2">
        <div class="flex items-center justify-between text-xs text-gray-600">
          <span>Pathway completion</span>
          <span class="font-semibold">
            {{ safePercent(summary.percent) }}%
          </span>
        </div>
        <div class="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-emerald-500 rounded-full transition-all"
            :style="{ width: `${safePercent(summary.percent)}%` }"
          />
        </div>
      </section>

      <!-- Items list -->
      <section class="space-y-3">
        <h2 class="text-sm font-semibold text-gray-800">
          Items in this pathway
        </h2>

        <div
          v-if="enrichedItems.length === 0"
          class="p-4 rounded bg-white border text-sm text-gray-600"
        >
          No items are configured for this pathway yet.
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="item in enrichedItems"
            :key="item.id"
            class="bg-white border rounded-xl p-3 flex flex-col gap-2 sm:flex-row sm:items-center"
          >
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <div class="text-xs text-gray-400">
                  #{{ item.order || 0 }}
                </div>
                <div class="font-medium truncate">
                  <span v-if="item.module?.title">
                    {{ item.module.title }}
                  </span>
                  <span v-else-if="item.sop_label">
                    SOP: {{ item.sop_label }}
                  </span>
                  <span v-else>
                    Item {{ item.id }}
                  </span>
                </div>
                <span
                  v-if="item.required"
                  class="inline-flex items-center rounded-full bg-amber-50 text-amber-700 px-2 py-0.5 text-[10px]"
                >
                  Required
                </span>
              </div>

              <div class="mt-0.5 text-xs text-gray-500 line-clamp-2" v-if="item.notes">
                {{ item.notes }}
              </div>
            </div>

            <!-- Status + actions -->
            <div class="flex flex-col items-end gap-1 min-w-[9rem]">
              <span
                class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
                :class="statusBadgeClass(item._status)"
              >
                {{ statusLabel(item._status) }}
              </span>

              <div v-if="item._attempt" class="text-[11px] text-gray-500 text-right">
                <div>Last score: {{ item._attempt.score }}%</div>
              </div>

              <button
                v-if="item.module?.id"
                type="button"
                class="mt-1 inline-flex items-center px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
                @click="goToModule(item)"
              >
                Go to module
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Optional debug -->
      <section class="space-y-1 text-[10px] text-gray-500">
        <div class="font-semibold">
          Raw pathway detail (debug)
        </div>
        <pre class="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto max-h-64">
{{ JSON.stringify(pathway, null, 2) }}
        </pre>
      </section>
    </div>
  </div>
</template>
