// frontend/composables/useCurrentUser.js
export function useCurrentUser () {
  const { get } = useApi()

  // Shared across the app thanks to useState
  const userState = useState('currentUser', () => ({
    loaded: false,
    loading: false,
    data: null,
    error: null
  }))

  async function fetchUser () {
    // Avoid spamming /whoami on every page
    if (userState.value.loaded || userState.value.loading) {
      return userState.value
    }

    userState.value.loading = true
    userState.value.error = null

    try {
      const data = await get('/whoami/')
      userState.value.data = data
    } catch (e) {
      userState.value.error = e && e.data
        ? JSON.stringify(e.data)
        : (e && e.message ? e.message : 'Failed to load user')
    } finally {
      userState.value.loaded = true
      userState.value.loading = false
    }

    return userState.value
  }

  return {
    userState,
    fetchUser
  }
}
