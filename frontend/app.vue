<template>
  <div class="min-h-screen flex bg-gray-100 text-gray-800">
    <!-- DESKTOP SIDEBAR -->
    <aside class="w-60 bg-white border-r shadow-sm hidden md:flex flex-col">
      <div class="p-4 text-xl font-bold text-emerald-700">
        MATRIX
      </div>

      <nav class="flex-1 overflow-y-auto">
        <ul class="flex flex-col gap-1 p-2">
          <!-- Main section -->
          <li v-for="link in mainLinks" :key="link.to">
            <NuxtLink
              :to="link.to"
              :class="linkClasses(link.to)"
            >
              <span v-if="link.icon" :class="link.icon"></span>
              <span>{{ link.label }}</span>
            </NuxtLink>
          </li>

          <div class="mt-4 border-t pt-3 text-xs font-semibold px-2 text-gray-500">
            Organisation
          </div>

          <li v-for="link in orgLinks" :key="link.to">
            <NuxtLink
              :to="link.to"
              :class="linkClasses(link.to)"
            >
              <span v-if="link.icon" :class="link.icon"></span>
              <span>{{ link.label }}</span>
            </NuxtLink>
          </li>

          <div class="mt-4 border-t pt-3 text-xs font-semibold px-2 text-gray-500">
            System
          </div>

          <li v-for="link in systemLinks" :key="link.to">
            <NuxtLink
              :to="link.to"
              :class="linkClasses(link.to)"
            >
              <span v-if="link.icon" :class="link.icon"></span>
              <span>{{ link.label }}</span>
            </NuxtLink>
          </li>
        </ul>
      </nav>

      <div class="p-3 border-t">
        <button
          v-if="auth.loggedIn"
          @click="logout"
          class="w-full px-3 py-2 text-sm rounded bg-red-600 text-white hover:bg-red-700"
        >
          Logout
        </button>
        <NuxtLink
          v-else
          to="/login"
          class="block w-full text-center py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700"
        >
          Login
        </NuxtLink>
      </div>
    </aside>

    <!-- MOBILE OVERLAY -->
    <transition name="fade">
      <div
        v-if="mobileMenu"
        class="fixed inset-0 bg-black/40 z-30 md:hidden"
        @click="mobileMenu = false"
      />
    </transition>

    <!-- MOBILE SIDEBAR -->
    <transition name="slide">
      <aside
        v-if="mobileMenu"
        class="fixed inset-y-0 left-0 w-64 bg-white border-r shadow-xl z-40 md:hidden flex flex-col"
      >
        <div class="p-4 text-xl font-bold text-emerald-700">
          MATRIX
        </div>

        <nav class="flex-1 overflow-y-auto">
          <ul class="flex flex-col gap-1 p-2">
            <li v-for="link in mainLinks" :key="'m-' + link.to">
              <NuxtLink
                :to="link.to"
                :class="linkClasses(link.to)"
                @click="mobileMenu = false"
              >
                <span v-if="link.icon" :class="link.icon"></span>
                <span>{{ link.label }}</span>
              </NuxtLink>
            </li>

            <div class="mt-4 border-t pt-3 text-xs font-semibold px-2 text-gray-500">
              Organisation
            </div>

            <li v-for="link in orgLinks" :key="'m-' + link.to">
              <NuxtLink
                :to="link.to"
                :class="linkClasses(link.to)"
                @click="mobileMenu = false"
              >
                <span v-if="link.icon" :class="link.icon"></span>
                <span>{{ link.label }}</span>
              </NuxtLink>
            </li>

            <div class="mt-4 border-t pt-3 text-xs font-semibold px-2 text-gray-500">
              System
            </div>

            <li v-for="link in systemLinks" :key="'m-' + link.to">
              <NuxtLink
                :to="link.to"
                :class="linkClasses(link.to)"
                @click="mobileMenu = false"
              >
                <span v-if="link.icon" :class="link.icon"></span>
                <span>{{ link.label }}</span>
              </NuxtLink>
            </li>
          </ul>
        </nav>

        <div class="p-3 border-t">
          <button
            v-if="auth.loggedIn"
            @click="() => { mobileMenu = false; logout(); }"
            class="w-full px-3 py-2 text-sm rounded bg-red-600 text-white hover:bg-red-700"
          >
            Logout
          </button>
          <NuxtLink
            v-else
            to="/login"
            class="block w-full text-center py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700"
            @click="mobileMenu = false"
          >
            Login
          </NuxtLink>
        </div>
      </aside>
    </transition>

    <!-- MAIN CONTENT AREA -->
    <div class="flex-1 flex flex-col min-h-screen">
      <!-- TOP BAR -->
      <header class="h-14 bg-white border-b shadow-sm flex items-center px-4">
        <button
          class="md:hidden p-2 mr-2"
          @click="mobileMenu = true"
        >
          <span class="i-lucide-menu text-xl"></span>
        </button>

        <h1 class="font-medium text-lg">
          {{ pageTitle }}
        </h1>

        <div class="ml-auto flex items-center gap-3">
          <span class="text-sm text-gray-600">
            {{ auth.user?.username }}
          </span>
        </div>
      </header>

      <!-- ROUTED PAGE -->
      <main class="flex-1 p-4">
        <NuxtPage />
      </main>
    </div>
  </div>
</template>

<script setup>
const auth = useAuth()
const route = useRoute()
const mobileMenu = ref(false)

const mainLinks = [
  { to: '/', label: 'Dashboard', icon: 'i-lucide-home' },
  { to: '/sops', label: 'SOPs', icon: 'i-lucide-file-text' },
  { to: '/modules', label: 'Modules', icon: 'i-lucide-book-open' },
  { to: '/skills', label: 'Skills', icon: 'i-lucide-badge-check' },
  { to: '/roles', label: 'Job Roles', icon: 'i-lucide-users' },
  { to: '/leaderboard', label: 'Leaderboards', icon: 'i-lucide-bar-chart' },
]

const orgLinks = [
  { to: '/users', label: 'Users', icon: 'i-lucide-user-circle' },
  { to: '/teams', label: 'Teams', icon: 'i-lucide-users-round' },
  { to: '/departments', label: 'Departments', icon: 'i-lucide-layout-grid' },
]

const systemLinks = [
  { to: '/settings', label: 'Settings', icon: 'i-lucide-settings' },
]

const pageTitle = computed(() => {
  const map = {
    '/': 'Dashboard',
    '/sops': 'SOPs',
    '/modules': 'Modules',
    '/skills': 'Skills',
    '/roles': 'Roles',
    '/leaderboard': 'Leaderboards',
    '/users': 'Users',
    '/teams': 'Teams',
    '/departments': 'Departments',
    '/settings': 'Settings',
    '/login': 'Login',
  }
  return map[route.path] || 'Matrix'
})

function linkClasses(path) {
  const isActive =
    route.path === path ||
    (path !== '/' && route.path.startsWith(path + '/'))

  return [
    'px-3 py-2 rounded flex items-center gap-2 text-sm transition-colors',
    isActive
      ? 'bg-emerald-50 text-emerald-700 font-medium'
      : 'hover:bg-gray-100 text-gray-700',
  ]
}

function logout() {
  auth.logout?.()
  navigateTo('/login')
}
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease;
}
.slide-enter-from {
  transform: translateX(-100%);
}
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
