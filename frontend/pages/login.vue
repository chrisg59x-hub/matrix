<script setup lang="ts">
const { login, error, loading } = useAuth()
const username = ref('employee')
const password = ref('employee123')
async function submit() {
  await login(username.value, password.value)
  return navigateTo('/')
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-10 space-y-3">
    <h1 class="text-xl font-semibold">Sign in</h1>
    <input v-model="username" class="border rounded p-2 w-full" placeholder="Username" />
    <input v-model="password" type="password" class="border rounded p-2 w-full" placeholder="Password" />
    <button :disabled="loading" @click="submit" class="w-full bg-black text-white rounded py-2">
      {{ loading ? 'Signing in…' : 'Sign in' }}
    </button>
    <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
  </div>
</template>
