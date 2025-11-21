// frontend/composables/useApi.ts
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export function useApi () {
  const config = useRuntimeConfig()
  // use your existing auth composable (auto-imported by Nuxt)
  const auth = useAuth()

  const baseURL =
    (config.public.apiBase as string | undefined) ||
    'http://127.0.0.1:8000/api'

  async function request (
    path: string,
    options: {
      method?: HttpMethod
      query?: any
      body?: any
      headers?: Record<string, string>
    } = {}
  ) {
    const url = baseURL + path

    // auth.token from your composable: it’s a Ref<string | null>
    const rawToken = (auth as any).token
    const token =
      typeof rawToken === 'string'
        ? rawToken
        : rawToken?.value ?? null

    const headers: Record<string, string> = {
      ...(options.headers || {}),
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    return await $fetch(url, {
      method: options.method || 'GET',
      headers,
      query: options.query,
      body: options.body,
    })
  }

  function get (path: string, query?: any) {
    return request(path, { method: 'GET', query })
  }

  function post (path: string, body?: any) {
    return request(path, { method: 'POST', body })
  }

  function put (path: string, body?: any) {
    return request(path, { method: 'PUT', body })
  }

  function patch (path: string, body?: any) {
    return request(path, { method: 'PATCH', body })
  }

  function del (path: string, body?: any) {
    return request(path, { method: 'DELETE', body })
  }

  return {
    request,
    get,
    post,
    put,
    patch,
    del,
  }
}
