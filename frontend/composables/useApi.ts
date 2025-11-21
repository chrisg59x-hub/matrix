// composables/useApi.ts
export function useApi() {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase
  const auth = useAuth()

  async function request<T = any>(
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    url: string,
    body?: any,
    opts: any = {},
  ): Promise<T> {
    const headers: Record<string, string> = {}

    // Attach JSON header unless it's FormData
    if (body !== undefined && !(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }

    const token = auth.token?.value
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return await $fetch<T>(url, {
      baseURL,
      method,
      body,
      headers,
      ...opts,
    })
  }

  return {
    get<T = any>(url: string, opts?: any) {
      return request<T>('GET', url, undefined, opts)
    },
    post<T = any>(url: string, body?: any, opts?: any) {
      return request<T>('POST', url, body, opts)
    },
    put<T = any>(url: string, body?: any, opts?: any) {
      return request<T>('PUT', url, body, opts)
    },
    patch<T = any>(url: string, body?: any, opts?: any) {
      return request<T>('PATCH', url, body, opts)
    },
    del<T = any>(url: string, opts?: any) {
      return request<T>('DELETE', url, undefined, opts)
    },
  }
}

