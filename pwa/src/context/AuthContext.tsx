import { createContext, useContext, useState, type ReactNode } from 'react'
import { getAuth, setAuth, clearAuth, type AuthData } from '../lib/auth'

interface AuthContextValue {
  auth: AuthData | null
  signIn: (data: AuthData) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuthState] = useState<AuthData | null>(getAuth)

  const signIn = (data: AuthData) => {
    setAuth(data)
    setAuthState(data)
  }

  const signOut = () => {
    clearAuth()
    setAuthState(null)
  }

  return (
    <AuthContext.Provider value={{ auth, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
