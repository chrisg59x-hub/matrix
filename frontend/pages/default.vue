<template>
  <div class="min-h-screen">
    <header class="px-4 py-3 border-b flex items-center gap-4">
      <NuxtLink to="/dashboard">Dashboard</NuxtLink>
      <NuxtLink to="/progress">My Progress</NuxtLink>
      <NuxtLink to="/leaderboard">Leaderboard</NuxtLink>
      <span class="ml-auto text-sm text-gray-600">Matrix SOPRPG</span>
    </header>
    <main class="p-4 max-w-5xl mx-auto">
      <slot />
    </main>
  </div>
</template>
