// composables/useApi.ts
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase || 'http://127.0.0.1:8000/api'

  // token + refresh live in global state + localStorage
  const token = useState<string | null>('token', () =>
    process.client ? localStorage.getItem('token') : null
  )
  const refresh = useState<string | null>('refresh', () =>
    process.client ? localStorage.getItem('refresh') : null
  )

  async function refreshTokenOnce(): Promise<boolean> {
    if (!refresh.value) return false
    try {
      const res = await $fetch<{ access: string }>(
        '/auth/token/refresh/',
        {
          method: 'POST',
          baseURL,
          body: { refresh: refresh.value },
          headers: { 'Content-Type': 'application/json' },
        }
      )
      token.value = res.access
      if (process.client) localStorage.setItem('token', res.access)
      return true
    } catch {
      // refresh failed – clear tokens
      token.value = null
      refresh.value = null
      if (process.client) {
        localStorage.removeItem('token')
        localStorage.removeItem('refresh')
      }
      return false
    }
  }

  async function request<T>(method: 'GET' | 'POST' | 'PATCH' | 'DELETE', url: string, body?: any): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }

    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }
    console.log('API request', method, url, headers)  // 👈 add this
    console.log('API request', method, url, headers)  // 👈 add this

    try {
      return await $fetch<T>(url, {
        method,
        baseURL,
        body,
        headers,
      })
    } catch (e: any) {
      // If unauthorized, try a single refresh -> retry once
      if (e?.status === 401) {
        const ok = await refreshTokenOnce()
        if (ok) {
          return await $fetch<T>(url, {
            method,
            baseURL,
            body,
            headers,
          })
        }
      }
      throw e
    }
  }

  return {
    token,
    baseURL,
    get<T>(url: string) { return request<T>('GET', url) },
    post<T>(url: string, body?: any) { return request<T>('POST', url, body) },
  }
}

