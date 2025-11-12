<script setup lang="ts">
const { user, logout } = useAuth()
</script>

<template>
  <header class="px-4 py-3 border-b flex items-center gap-4">
    <NuxtLink to="/dashboard">Dashboard</NuxtLink>
    <NuxtLink to="/sops">SOPs</NuxtLink>
    <NuxtLink to="/progress">My Progress</NuxtLink>
    <NuxtLink to="/leaderboard">Leaderboard</NuxtLink>

    <NuxtLink v-if="user && ['manager','admin'].includes(user.biz_role||'')" to="/admin/sops">SOP Admin</NuxtLink>
    <NuxtLink v-if="user && ['manager','admin'].includes(user.biz_role||'')" to="/admin/levels">Levels</NuxtLink>

    <div class="ml-auto flex items-center gap-3 text-sm">
      <span v-if="user">Signed in: <b>{{ user.username }}</b>
        <span v-if="user.biz_role" class="ml-1 px-2 py-0.5 text-xs rounded bg-gray-200">{{ user.biz_role }}</span>
      </span>
      <NuxtLink v-else to="/login">Login</NuxtLink>
      <button v-if="user" class="border rounded px-2 py-1" @click="logout(); navigateTo('/login')">Logout</button>
    </div>
  </header>
  <main class="p-4 max-w-6xl mx-auto"><slot/></main>
</template>

