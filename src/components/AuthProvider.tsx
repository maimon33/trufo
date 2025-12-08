import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, getCurrentUser, setCurrentUser, signInWithGoogle, signOut } from '../lib/auth'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  signIn: () => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Load user from localStorage on app start
    const storedUser = getCurrentUser()
    setUser(storedUser)
    setIsLoading(false)
  }, [])

  const handleSignIn = async () => {
    setIsLoading(true)
    try {
      const user = await signInWithGoogle()
      setUser(user)
    } catch (error) {
      console.error('Sign in failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignOut = () => {
    signOut()
    setUser(null)
  }

  const value: AuthContextType = {
    user,
    isLoading,
    signIn: handleSignIn,
    signOut: handleSignOut
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}