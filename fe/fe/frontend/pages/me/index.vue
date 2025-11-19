<script setup>
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        My training
      </h1>
      <p class="text-sm text-gray-600">
        Shortcuts to your personal dashboard and recent quiz activity.
      </p>
    </header>

    <section class="grid gap-4 sm:grid-cols-2">
      <!-- My dashboard -->
      <NuxtLink
        to="/me/dashboard"
        class="block bg-white rounded-xl shadow p-4 hover:shadow-md transition text-sm"
      >
        <div class="font-semibold text-gray-900 mb-1">
          My dashboard
        </div>
        <p class="text-gray-600 text-xs mb-2">
          See your XP, level, quiz performance, and any overdue training.
        </p>
        <div class="text-[11px] text-emerald-700 font-medium">
          Go to my dashboard →
        </div>
      </NuxtLink>

      <!-- My attempts -->
      <NuxtLink
        to="/me/attempts"
        class="block bg-white rounded-xl shadow p-4 hover:shadow-md transition text-sm"
      >
        <div class="font-semibold text-gray-900 mb-1">
          My attempts
        </div>
        <p class="text-gray-600 text-xs mb-2">
          Review your recent quiz attempts and open detailed per-question feedback.
        </p>
        <div class="text-[11px] text-emerald-700 font-medium">
          View my attempts →
        </div>
      </NuxtLink>
    </section>

    <!-- Optional extra links area (easy to expand later) -->
    <section class="space-y-2 text-xs text-gray-600">
      <h2 class="text-sm font-semibold text-gray-800">
        More training features
      </h2>
      <ul class="list-disc list-inside space-y-1">
        <li>
          Use the <span class="font-medium">Modules</span> section to start new training quizzes.
        </li>
        <li>
          Your XP and level will update automatically as you pass modules and gain sign-offs.
        </li>
      </ul>
    </section>
  </div>
</template>
