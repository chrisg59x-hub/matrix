<!-- frontend/pages/login.vue -->
<script setup lang="ts">
const auth = useAuth()
const router = useRouter()

const username = ref('')
const password = ref('')

const submitting = ref(false)
const error = ref<string | null>(null)

async function submit (e?: Event) {
  e?.preventDefault()

  error.value = null
  submitting.value = true

  try {
    // Call the auth composable's login
    const ok = await auth.login(username.value, password.value)

    if (!ok) {
      // If useAuth tracks its own error, surface it
      const authError = (auth as any).error
      if (authError && 'value' in authError) {
        error.value = authError.value || 'Login failed'
      } else {
        error.value = 'Login failed'
      }
      return
    }

    // Success → go to dashboard (or whatever route you prefer)
    router.push('/')
  } catch (err: any) {
    console.error('Login failed', err)
    error.value = err?.data?.detail || err?.message || 'Login failed'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <form
      class="bg-white shadow rounded-lg p-6 w-full max-w-sm space-y-4"
      @submit="submit"
    >
      <h1 class="text-lg font-semibold text-gray-800">
        Matrix Login
      </h1>

      <div v-if="error" class="text-sm text-red-600">
        {{ error }}
      </div>

      <div class="space-y-1">
        <label class="block text-xs font-medium text-gray-600">
          Username
        </label>
        <input
          v-model="username"
          type="text"
          class="w-full border rounded px-3 py-2 text-sm"
          autocomplete="username"
        >
      </div>

      <div class="space-y-1">
        <label class="block text-xs font-medium text-gray-600">
          Password
        </label>
        <input
          v-model="password"
          type="password"
          class="w-full border rounded px-3 py-2 text-sm"
          autocomplete="current-password"
        >
      </div>

      <button
        type="submit"
        class="w-full px-3 py-2 text-sm rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
        :disabled="submitting"
      >
        {{ submitting ? 'Signing in…' : 'Login' }}
      </button>
    </form>
  </div>
</template>
