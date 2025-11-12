
export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path === '/login') return
  const { token, user, me } = useAuth()
  if (token.value && !user.value) {
    try { await me() } catch {}
  }
  if (!token.value) return navigateTo('/login')
})