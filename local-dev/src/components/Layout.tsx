import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from './AuthProvider'

interface LayoutProps {
  children: ReactNode
  title?: string
}

export default function Layout({ children, title = 'Trufo' }: LayoutProps) {
  const { user, signOut } = useAuth()
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-gray-900">
                <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                Trufo
              </Link>
              {user && (
                <div className="hidden md:flex space-x-4">
                  <Link
                    to="/create"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Create Object
                  </Link>
                  <Link
                    to="/manage"
                    className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    My Objects
                  </Link>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <div className="flex items-center space-x-3">
                    {user.picture && (
                      <img
                        src={user.picture}
                        alt={user.name}
                        className="w-8 h-8 rounded-full"
                      />
                    )}
                    <div className="text-sm">
                      <div className="font-medium text-gray-900">{user.name}</div>
                      <div className="text-gray-500">{user.email}</div>
                    </div>
                  </div>
                  <button
                    onClick={signOut}
                    className="bg-gray-500 hover:bg-gray-600 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <div className="text-sm text-gray-600">
                  Sign in to create and manage objects
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        {title && (
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            {title}
          </h1>
        )}
        {children}
      </main>
    </div>
  )
}