import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { api } from './lib/api'
import SignIn from './pages/SignIn'
import Home from './pages/Home'
import Create from './pages/Create'
import Access from './pages/Access'

function MagicLinkHandler({ children }: { children: React.ReactNode }) {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const authToken = params.get('auth')
    if (!authToken) return

    // Remove the ?auth= param from the URL immediately
    const clean = new URL(window.location.href)
    clean.searchParams.delete('auth')
    window.history.replaceState({}, '', clean.toString())

    api.verifyMagicLink(authToken)
      .then(res => {
        signIn({ email: res.email, secret: res.userSecret })
        navigate('/', { replace: true })
      })
      .catch(() => navigate('/signin', { replace: true }))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { auth } = useAuth()
  return auth ? <>{children}</> : <Navigate to="/signin" replace />
}

export default function App() {
  return (
    <BrowserRouter basename="/app">
      <AuthProvider>
        <MagicLinkHandler>
          <Routes>
            <Route path="/signin" element={<SignIn />} />
            <Route path="/access/:token" element={<Access />} />
            <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
            <Route path="/create" element={<RequireAuth><Create /></RequireAuth>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </MagicLinkHandler>
      </AuthProvider>
    </BrowserRouter>
  )
}
