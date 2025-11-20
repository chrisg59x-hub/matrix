<!-- frontend/pages/roles/index.vue -->
<script setup lang="ts">
const { get } = useApi()

type RoleRow = {
  id: string
  name: string
  is_active: boolean
}

type RoleSkillRow = {
  id: string
  role: string
  role_name?: string | null
  skill: string
  skill_name?: string | null
  required: boolean
}

const loading = ref(true)
const err = ref<string | null>(null)
const roles = ref<RoleRow[]>([])
const roleSkills = ref<RoleSkillRow[]>([])

// simple filter dropdown
const activeFilter = ref<'all' | 'active' | 'inactive'>('all')

onMounted(loadAll)

async function loadAll () {
  loading.value = true
  err.value = null
  try {
    await Promise.all([
      loadRoles(),
      loadRoleSkills(),
    ])
  } catch (e: any) {
    err.value = e?.data
      ? JSON.stringify(e.data)
      : (e?.message || 'Failed to load roles')
  } finally {
    loading.value = false
  }
}

async function loadRoles () {
  const data: any = await get('/roles/')
  roles.value = Array.isArray(data) ? data : (data.results || [])
}

async function loadRoleSkills () {
  const data: any = await get('/role-skills/')
  roleSkills.value = Array.isArray(data) ? data : (data.results || [])
}

const rolesWithSkills = computed(() => {
  // index roleSkills by role id
  const byRole: Record<string, RoleSkillRow[]> = {}
  for (const rs of roleSkills.value) {
    const key = String(rs.role)
    if (!byRole[key]) byRole[key] = []
    byRole[key].push(rs)
  }

  // merge into role objects
  return roles.value
    .filter(r => {
      if (activeFilter.value === 'all') return true
      if (activeFilter.value === 'active') return r.is_active
      return !r.is_active
    })
    .map(r => ({
      ...r,
      skills: (byRole[String(r.id)] || []).slice().sort((a, b) => {
        const an = (a.skill_name || '').toLowerCase()
        const bn = (b.skill_name || '').toLowerCase()
        return an.localeCompare(bn)
      }),
    }))
})
</script>

<template>
  <div class="max-w-6xl mx-auto space-y-4">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">
          Job roles
        </h1>
        <p class="text-sm text-gray-600">
          Roles in your organisation and the skills required for each.
        </p>
      </div>

      <div class="flex flex-wrap gap-2 sm:items-center">
        <select
          v-model="activeFilter"
          class="border rounded px-2 py-1.5 text-xs"
        >
          <option value="all">
            All roles
          </option>
          <option value="active">
            Active only
          </option>
          <option value="inactive">
            Inactive only
          </option>
        </select>

        <button
          type="button"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
          @click="loadAll"
        >
          Refresh
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-sm text-gray-500">
      Loading roles…
    </div>

    <div v-else-if="err" class="text-sm text-red-600 break-all">
      {{ err }}
    </div>

    <div v-else>
      <div v-if="rolesWithSkills.length === 0" class="text-sm text-gray-600">
        No roles match your filter.
      </div>

      <div class="space-y-3">
        <div
          v-for="role in rolesWithSkills"
          :key="role.id"
          class="bg-white border rounded-xl shadow-sm p-4 space-y-2"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <div class="font-semibold text-gray-900">
                {{ role.name }}
              </div>
              <div class="text-xs text-gray-500">
                Role ID:
                <span class="font-mono">{{ role.id }}</span>
              </div>
            </div>

            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-[11px]"
              :class="role.is_active
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                : 'bg-gray-100 text-gray-600 border border-gray-200'"
            >
              {{ role.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>

          <div class="pt-1">
            <div class="text-xs font-semibold text-gray-600 mb-1">
              Required skills
            </div>

            <div v-if="!role.skills.length" class="text-xs text-gray-500">
              No skills linked to this role yet.
            </div>

            <ul
              v-else
              class="flex flex-wrap gap-1"
            >
              <li
                v-for="rs in role.skills"
                :key="rs.id"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] border"
                :class="rs.required
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-gray-50 text-gray-600 border-gray-200'"
              >
                <span class="mr-1">
                  {{ rs.skill_name || 'Skill ' + rs.skill }}
                </span>
                <span
                  v-if="!rs.required"
                  class="text-[10px] uppercase tracking-wide"
                >
                  optional
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
