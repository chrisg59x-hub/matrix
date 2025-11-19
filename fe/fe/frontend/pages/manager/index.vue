<script setup>
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <header class="space-y-1">
      <h1 class="text-2xl font-bold">
        Manager area
      </h1>
      <p class="text-sm text-gray-600">
        Tools for tracking training performance and managing your organisation.
      </p>
    </header>

    <!-- Primary tiles -->
    <section class="grid gap-4 sm:grid-cols-2 md:grid-cols-3">
      <!-- Manager dashboard -->
      <NuxtLink
        to="/manager/dashboard"
        class="block bg-white rounded-xl shadow p-4 hover:shadow-md transition text-sm"
      >
        <div class="font-semibold text-gray-900 mb-1">
          Manager dashboard
        </div>
        <p class="text-gray-600 text-xs mb-2">
          View organisation-wide training stats, pass rates, and XP totals.
        </p>
        <div class="text-[11px] text-emerald-700 font-medium">
          Open manager dashboard →
        </div>
      </NuxtLink>

      <!-- Modules admin (if you’re using /modules as manager UI) -->
      <NuxtLink
        to="/modules"
        class="block bg-white rounded-xl shadow p-4 hover:shadow-md transition text-sm"
      >
        <div class="font-semibold text-gray-900 mb-1">
          Training modules
        </div>
        <p class="text-gray-600 text-xs mb-2">
          Create and manage quiz modules, SOP-linked training, and difficulty levels.
        </p>
        <div class="text-[11px] text-emerald-700 font-medium">
          Manage modules →
        </div>
      </NuxtLink>

      <!-- Teams / departments overview (you can wire these up later) -->
      <NuxtLink
        to="/teams"
        class="block bg-white rounded-xl shadow p-4 hover:shadow-md transition text-sm"
      >
        <div class="font-semibold text-gray-900 mb-1">
          Teams & departments
        </div>
        <p class="text-gray-600 text-xs mb-2">
          Assign users to teams, departments, and track XP at group level.
        </p>
        <div class="text-[11px] text-emerald-700 font-medium">
          Manage teams →
        </div>
      </NuxtLink>
    </section>

    <!-- Helper text / notes -->
    <section class="space-y-2 text-xs text-gray-600">
      <h2 class="text-sm font-semibold text-gray-800">
        About this area
      </h2>
      <ul class="list-disc list-inside space-y-1">
        <li>
          Access to this area and the manager dashboard is controlled server-side
          (only users with <code class="bg-gray-100 px-1 rounded">biz_role = "manager"</code>
          or <code class="bg-gray-100 px-1 rounded">"admin"</code> can use it).
        </li>
        <li>
          Use the dashboard to spot low pass-rates, high-risk areas, or teams needing
          additional coaching.
        </li>
        <li>
          You can extend this page with more tiles (e.g. <span class="font-medium">Pathways</span>,
          <span class="font-medium">Badges</span>, or <span class="font-medium">Recert rules</span>)
          as those features grow.
        </li>
      </ul>
    </section>
  </div>
</template>
