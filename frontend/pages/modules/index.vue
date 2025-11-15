<script setup lang="ts">
const route = useRoute()
const { get, post } = useApi()

type ModuleRow = {
  id: string
  title?: string
  description?: string
  code?: string
  skill?: string | null
  skill_name?: string | null
  active?: boolean
}

const modules = ref<ModuleRow[]>([])
const loading = ref(true)
const err = ref<string | null>(null)

const skillFilter = computed(() => route.query.skill || null)

onMounted(load)

async function load() {
  loading.value = true
  err.value = null

  try {
    let url = "/modules/"

    if (skillFilter.value) {
      url += `?skill=${encodeURIComponent(String(skillFilter.value))}`
    }

    const data = await get(url)
    modules.value = Array.isArray(data) ? data : (data.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : e?.message || "Failed to load modules"
  } finally {
    loading.value = false
  }
}

async function startModule(m: ModuleRow) {
  try {
    const resp = await post(`/modules/${m.id}/start/`, {})

    // backend returns attempt_id + served questions
    if (resp?.attempt_id) {
      navigateTo(`/modules/${m.id}/attempt/${resp.attempt_id}`)
    }
  } catch (e) {
    console.error(e)
    alert("Could not start module.")
  }
}

function moduleTitle(m: ModuleRow) {
  return m.title || m.code || `Module ${m.id}`
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold">Training Modules</h1>
        <p class="text-sm text-gray-600">
          Select a module to begin training.
          <span v-if="skillFilter" class="font-semibold">(filtered by skill)</span>
        </p>
      </div>

      <button
        class="px-3 py-1.5 text-sm bg-white border rounded hover:bg-gray-50"
        @click="load"
      >
        Refresh
      </button>
    </div>

    <div v-if="loading" class="text-gray-500">Loading modules…</div>

    <div v-else-if="err" class="text-red-600 break-all">{{ err }}</div>

    <div v-else>
      <div v-if="modules.length === 0" class="text-sm text-gray-600">
        No modules found.
      </div>

      <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="m in modules"
          :key="m.id"
          class="bg-white border rounded p-4 shadow-sm flex flex-col gap-2"
        >
          <header class="flex justify-between">
            <div>
              <h2 class="font-semibold">{{ moduleTitle(m) }}</h2>
              <p
                v-if="m.skill_name"
                class="text-xs text-emerald-700"
              >
                Skill: {{ m.skill_name }}
              </p>
            </div>

            <span
              class="px-2 py-0.5 text-[11px] rounded-full"
              :class="m.active === false
                ? 'bg-gray-100 text-gray-500'
                : 'bg-emerald-50 text-emerald-700'"
            >
              {{ m.active === false ? 'Inactive' : 'Active' }}
            </span>
          </header>

          <p
            v-if="m.description"
            class="text-xs text-gray-600 line-clamp-3"
          >
            {{ m.description }}
          </p>

          <div class="mt-2 flex justify-between text-xs">
            <NuxtLink
              :to="`/modules/${m.id}`"
              class="underline text-emerald-700 hover:text-emerald-900"
            >
              View details
            </NuxtLink>

            <button
              class="px-3 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700"
              @click="startModule(m)"
            >
              Start / Continue
            </button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
