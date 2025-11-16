<!-- components/DashboardTrainingCard.vue -->
<script setup lang="ts">
const { get } = useApi()
const router = useRouter()

const loading = ref(true)
const err = ref<string | null>(null)

const overdueRequirements = ref(0)
const overdueModules = ref(0)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null

  try {
    const [reqData, modData] = await Promise.all([
      get('/me/overdue-sops/'),
      get('/modules/?onlyOverdue=1'),
    ])

    const reqs = Array.isArray(reqData) ? reqData : (reqData.results || [])
    const mods = Array.isArray(modData) ? modData : (modData.results || [])

    overdueRequirements.value = reqs.length
    overdueModules.value = mods.length
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load training summary')
  } finally {
    loading.value = false
  }
}

function goToOverdue () {
  router.push('/overdue')
}

function goToOverdueModules () {
  router.push('/modules?onlyOverdue=1')
}
</script>

<template>
  <div class="bg-white border rounded-xl p-4 shadow-sm flex flex-col gap-3">
    <div class="flex items-center justify-between gap-2">
      <div>
        <h2 class="text-base font-semibold">
          Training Overview
        </h2>
        <p class="text-xs text-gray-600">
          Quick snapshot of your overdue training and modules.
        </p>
      </div>

      <button
        type="button"
        class="px-2 py-1 text-[11px] rounded border bg-white hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="text-xs text-gray-500">
      Loading training summary…
    </div>

    <div v-else-if="err" class="text-xs text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex gap-4 text-sm">
        <div>
          <div class="text-[11px] text-gray-500 uppercase tracking-wide">
            Overdue requirements
          </div>
          <div class="mt-1 text-2xl font-bold text-emerald-700">
            {{ overdueRequirements }}
          </div>
          <div class="text-[11px] text-gray-500">
            SOP / skill requirements past due
          </div>
        </div>

        <div class="hidden sm:block w-px bg-gray-200" />

        <div>
          <div class="text-[11px] text-gray-500 uppercase tracking-wide">
            Overdue modules
          </div>
          <div class="mt-1 text-2xl font-bold" :class="overdueModules ? 'text-red-700' : 'text-gray-700'">
            {{ overdueModules }}
          </div>
          <div class="text-[11px] text-gray-500">
            Modules linked to overdue requirements
          </div>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 justify-end">
        <button
          type="button"
          class="px-3 py-1.5 text-xs rounded bg-emerald-600 text-white hover:bg-emerald-700"
          @click="goToOverdue"
        >
          View overdue training
        </button>

        <button
          type="button"
          class="px-3 py-1.5 text-xs rounded border text-emerald-700 hover:bg-emerald-50"
          @click="goToOverdueModules"
        >
          Overdue modules list
        </button>
      </div>
    </div>
  </div>
</template>
