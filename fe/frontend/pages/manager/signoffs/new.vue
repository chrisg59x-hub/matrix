<!-- frontend/pages/manager/signoffs/new.vue -->
<script setup lang="ts">
const { get, post } = useApi()
const router = useRouter()

type User = {
  id: string | number
  username: string
}

type Skill = {
  id: string | number
  name: string
}

const loading = ref(true)
const saving = ref(false)
const err = ref<string | null>(null)
const success = ref<string | null>(null)

const users = ref<User[]>([])
const skills = ref<Skill[]>([])

// form state
const selectedUserId = ref<string | number | null>(null)
const selectedSkillId = ref<string | number | null>(null)
const note = ref('')

// initial load of dropdown options
onMounted(loadOptions)

async function loadOptions () {
  loading.value = true
  err.value = null
  success.value = null

  try {
    const [usersData, skillsData]: any[] = await Promise.all([
      get('/users/'),
      get('/skills/'),
    ])

    users.value = Array.isArray(usersData)
      ? usersData
      : (usersData.results || [])

    skills.value = Array.isArray(skillsData)
      ? skillsData
      : (skillsData.results || [])
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to load users/skills')
  } finally {
    loading.value = false
  }
}

const canSave = computed(() =>
  !!selectedUserId.value && !!selectedSkillId.value && !saving.value,
)

async function submitForm () {
  if (!canSave.value) return

  saving.value = true
  err.value = null
  success.value = null

  try {
    await post('/signoffs/', {
      user: selectedUserId.value,
      skill: selectedSkillId.value,
      note: note.value || '',
    })

    success.value = 'Sign-off recorded successfully.'
    // optional: redirect back to list after a short delay
    setTimeout(() => {
      router.push('/manager/signoffs')
    }, 800)
  } catch (e: any) {
    err.value = e?.data ? JSON.stringify(e.data) : (e?.message || 'Failed to save sign-off')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        New supervisor sign-off
      </h1>
      <p class="text-sm text-gray-600">
        Record that a manager or supervisor has validated a user for a given skill.
      </p>
    </header>

    <div class="flex items-center gap-2">
      <NuxtLink
        to="/manager/signoffs"
        class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
      >
        ← Back to sign-offs
      </NuxtLink>
      <button
        type="button"
        class="px-3 py-1.5 text-xs rounded border bg-white hover:bg-gray-50"
        @click="loadOptions"
      >
        Reload options
      </button>
    </div>

    <div v-if="loading" class="p-4 rounded bg-gray-100 text-sm">
      Loading users and skills…
    </div>

    <div
      v-else
      class="space-y-4 bg-white border rounded-xl shadow p-4"
    >
      <div
        v-if="err"
        class="p-2 rounded bg-red-100 text-sm text-red-800 whitespace-pre-wrap"
      >
        {{ err }}
      </div>

      <div
        v-if="success"
        class="p-2 rounded bg-emerald-100 text-sm text-emerald-800"
      >
        {{ success }}
      </div>

      <!-- User -->
      <div class="space-y-1">
        <label class="text-xs font-medium text-gray-600">
          User to sign off
        </label>
        <select
          v-model="selectedUserId"
          class="border rounded px-2 py-1.5 text-sm w-full"
        >
          <option :value="null">
            Select a user…
          </option>
          <option
            v-for="u in users"
            :key="u.id"
            :value="u.id"
          >
            {{ u.username }} ({{ u.id }})
          </option>
        </select>
      </div>

      <!-- Skill -->
      <div class="space-y-1">
        <label class="text-xs font-medium text-gray-600">
          Skill
        </label>
        <select
          v-model="selectedSkillId"
          class="border rounded px-2 py-1.5 text-sm w-full"
        >
          <option :value="null">
            Select a skill…
          </option>
          <option
            v-for="s in skills"
            :key="s.id"
            :value="s.id"
          >
            {{ s.name }}
          </option>
        </select>
      </div>

      <!-- Note -->
      <div class="space-y-1">
        <label class="text-xs font-medium text-gray-600">
          Note (optional)
        </label>
        <textarea
          v-model="note"
          rows="3"
          class="border rounded px-2 py-1.5 text-sm w-full"
          placeholder="E.g. observed on-the-job, safe & competent on container unloading SOP..."
        />
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-2">
        <NuxtLink
          to="/manager/signoffs"
          class="px-3 py-1.5 text-sm rounded border bg-white hover:bg-gray-50"
        >
          Cancel
        </NuxtLink>
        <button
          type="button"
          class="px-4 py-1.5 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
          :disabled="!canSave"
          @click="submitForm"
        >
          <span v-if="saving">Saving…</span>
          <span v-else>Save sign-off</span>
        </button>
      </div>
    </div>
  </div>
</template>
