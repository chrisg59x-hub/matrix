<script setup lang="ts">
const route = useRoute()
const { get, post } = useApi()

type ModuleRow = {
  id: string | number
  title?: string
  name?: string
  description?: string
  code?: string
  skill_id?: string | number | null
  skill_name?: string | null
  active?: boolean
  // add more if your API returns them
}

const modules = ref<ModuleRow[]>([])
const loading = ref(true)
const err = ref<string | null>(null)

// optional filter coming from ?skill=<id>
const skillFilter = computed(() => route.query.skill || null)

onMounted(load)

async function load () {
  loading.value = true
  err.value = null

  try {
    // basic URL
    let url = '/modules/'

    // if backend supports filtering, you can append ?skill=<id> here
    if (skillFilter.value) {
      const qs = new URLSearchParams({ skill: String(skillFilter.value) })
      url += `?${qs.toString()}`
    }

    const data: any = await get(url)
    const items = Array.isArray(data) ? data : (data.results || [])
    modules.value = items
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load modules')
  } finally {
    loading.value = false
  }
}

function moduleTitle(m: ModuleRow) {
  return m.title || m.name || m.code || `Module #${m.id}`
}

function moduleDescription(m: ModuleRow) {
  return m.description || ''
}

function moduleSkill(m: ModuleRow) {
  return m.skill_name || (m.skill_id ? `Skill #${m.skill_id}` : '')
}

// Placeholder for starting / continuing a module attempt
async function startModule(m: ModuleRow) {
  try {
    // if you’ve wired up the /modules/<id>/start/ endpoint:
    // await post(`/modules/${m.id}/start/`, {})
    // For now just log / no-op
    console.log('Start module', m.id)
    // Later: navigateTo(`/modules/${m.id}`)
  } catch (e) {
    console.error(e)
    alert('Failed to start module (placeholder — wire backend later).')
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold">
          Training Modules
        </h1>
        <p class="text-sm text-gray-600 mt-1">
          Browse available training modules. This page will power the full training chain later.
          <span v-if="skillFilter" class="font-semibold">
            (filtered by skill: {{ skillFilter }})
          </span>
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

    <div v-if="loading" class="text-gray-500">
      Loading modules…
    </div>

    <div v-else-if="err" class="text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="modules.length === 0" class="text-sm text-gray-600">
        No modules found.
        <span v-if="skillFilter">
          (Try clearing the skill filter.)
        </span>
      </div>

      <div
        v-else
        class="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
      >
        <article
          v-for="m in modules"
          :key="m.id"
          class="bg-white border rounded-lg p-4 flex flex-col gap-2 shadow-sm"
        >
          <header class="flex items-start justify-between gap-2">
            <div>
              <h2 class="font-semibold text-sm md:text-base">
                {{ moduleTitle(m) }}
              </h2>
              <p
                v-if="moduleSkill(m)"
                class="text-xs text-emerald-700 mt-0.5"
              >
                Skill: {{ moduleSkill(m) }}
              </p>
            </div>

            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
              :class="m.active === false
                ? 'bg-gray-100 text-gray-500'
                : 'bg-emerald-50 text-emerald-700'"
            >
              {{ m.active === false ? 'Inactive' : 'Active' }}
            </span>
          </header>

          <p
            v-if="moduleDescription(m)"
            class="text-xs text-gray-600 line-clamp-3"
          >
            {{ moduleDescription(m) }}
          </p>

          <div class="mt-2 flex items-center justify-between gap-2 text-xs">
            <NuxtLink
              :to="`/modules/${m.id}`"
              class="underline text-emerald-700 hover:text-emerald-900"
            >
              View details
            </NuxtLink>

            <button
              type="button"
              class="px-3 py-1 rounded bg-emerald-600 text-white text-xs hover:bg-emerald-700"
              @click="startModule(m)"
            >
              Start / continue
            </button>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
