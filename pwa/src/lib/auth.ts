const AUTH_KEY = 'trufo_auth'

export interface AuthData {
  email: string
  secret: string
}

export function getAuth(): AuthData | null {
  try {
    const stored = localStorage.getItem(AUTH_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export function setAuth(data: AuthData): void {
  localStorage.setItem(AUTH_KEY, JSON.stringify(data))
}

export function clearAuth(): void {
  localStorage.removeItem(AUTH_KEY)
}
