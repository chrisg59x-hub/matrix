// composables/useAuth.ts
type TokenResp = { access: string; refresh?: string }
type Me = { username: string; biz_role: string | null }

export function useAuth() {
  const { post, get } = useApi()
  const token = useState<string | null>('token', () =>
    process.client ? localStorage.getItem('token') : null
  )
  const refresh = useState<string | null>('refresh', () =>
    process.client ? localStorage.getItem('refresh') : null
  )
  const user = useState<Me | null>('user', () => null)
  const loading = useState<boolean>('authLoading', () => false)
  const error = useState<string | null>('authError', () => null)

  async function login(username: string, password: string) {
    try {
      loading.value = true
      error.value = null
      const t = await post<TokenResp>('/auth/token/', { username, password })
      token.value = t.access
      if (t.refresh) refresh.value = t.refresh
      if (process.client) {
        localStorage.setItem('token', t.access)
        if (t.refresh) localStorage.setItem('refresh', t.refresh)
      }
      await me()
    } catch (e: any) {
      error.value = e?.data?.detail || 'Login failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function me() {
    const m = await get<Me>('/me/whoami/')
    user.value = m
    return m
  }

  function logout() {
    token.value = null
    refresh.value = null
    user.value = null
    if (process.client) {
      localStorage.removeItem('token')
      localStorage.removeItem('refresh')
    }
  }

  return { token, refresh, user, loading, error, login, logout, me }
}
