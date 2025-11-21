// frontend/composables/useAuth.ts
import { useApi } from './useApi'

type Me = {
  id: number
  username: string
  email?: string
  biz_role?: string
}

type TokenResp = {
  access: string
  refresh: string
}

export function useAuth () {
  const token   = useState<string | null>('auth-token',   () => null)
  const refresh = useState<string | null>('auth-refresh', () => null)
  const user    = useState<Me | null>('auth-user',        () => null)
  const loading = useState<boolean>('auth-loading',       () => false)
  const error   = useState<string | null>('auth-error',   () => null)

  const { get, post } = useApi()

  async function login (username: string, password: string) {
    loading.value = true
    error.value = null

    try {
      // ✅ This must match the backend route: /api/token/
      const t = await post<TokenResp>('/token/', { username, password })

      token.value = t.access
      refresh.value = t.refresh

      if (process.client) {
        localStorage.setItem('auth-token', t.access)
        localStorage.setItem('auth-refresh', t.refresh)
      }

      // Load current user
      const me = await get<Me>('/me/whoami/')
      user.value = me
    } catch (e: any) {
      console.error('Auth login error', e)
      error.value = e?.data?.detail || e?.message || 'Login failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  function logout () {
    token.value = null
    refresh.value = null
    user.value = null

    if (process.client) {
      localStorage.removeItem('auth-token')
      localStorage.removeItem('auth-refresh')
    }

    navigateTo('/login')
  }

  const loggedIn = computed(() => !!token.value)

  return { token, refresh, user, loading, error, login, logout, loggedIn }
}
