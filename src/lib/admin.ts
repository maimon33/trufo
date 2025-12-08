// Admin token management
const ADMIN_TOKEN_KEY = 'trufo_admin_token'
const S3_ADMIN_TOKEN_URL = `${import.meta.env.VITE_S3_BUCKET_URL}/admin/admin-token.txt`

export interface AdminAuth {
  isAdmin: boolean
  token: string | null
}

// Get stored admin token
export const getStoredAdminToken = (): string | null => {
  try {
    return localStorage.getItem(ADMIN_TOKEN_KEY)
  } catch {
    return null
  }
}

// Store admin token
export const storeAdminToken = (token: string): void => {
  try {
    localStorage.setItem(ADMIN_TOKEN_KEY, token)
  } catch (error) {
    console.error('Failed to store admin token:', error)
  }
}

// Clear admin token
export const clearAdminToken = (): void => {
  try {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
  } catch (error) {
    console.error('Failed to clear admin token:', error)
  }
}

// Verify admin token against S3 (or hardcoded for dev)
export const verifyAdminToken = async (token: string): Promise<boolean> => {
  // Development mode - accept hardcoded token
  if (import.meta.env.DEV && token.trim() === 'root') {
    console.log('Dev mode: Using hardcoded admin token')
    return true
  }

  try {
    const response = await fetch(S3_ADMIN_TOKEN_URL, {
      method: 'GET',
      cache: 'no-cache'
    })

    if (!response.ok) {
      console.error('Failed to fetch admin token from S3:', response.statusText)
      return false
    }

    const storedToken = (await response.text()).trim()
    return storedToken === token.trim()
  } catch (error) {
    console.error('Error verifying admin token:', error)
    return false
  }
}

// Check if current user has admin access
export const checkAdminAccess = async (): Promise<AdminAuth> => {
  const storedToken = getStoredAdminToken()

  if (!storedToken) {
    return { isAdmin: false, token: null }
  }

  const isValid = await verifyAdminToken(storedToken)

  if (!isValid) {
    clearAdminToken()
    return { isAdmin: false, token: null }
  }

  return { isAdmin: true, token: storedToken }
}

// Authenticate as admin with token
export const authenticateAdmin = async (token: string): Promise<boolean> => {
  const isValid = await verifyAdminToken(token)

  if (isValid) {
    storeAdminToken(token)
    return true
  }

  return false
}