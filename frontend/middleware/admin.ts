export default defineNuxtRouteMiddleware(async (to) => {
  if (!to.path.startsWith('/admin')) return
  const { token, user, me } = useAuth()
  if (token.value && !user.value) { try { await me() } catch {} }
  const role = user.value?.biz_role || ''
  if (!['manager','admin'].includes(role)) return navigateTo('/dashboard')
})