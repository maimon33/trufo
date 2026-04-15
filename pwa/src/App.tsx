import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { api } from './lib/api'
import SignIn from './pages/SignIn'
import Home from './pages/Home'
import Create from './pages/Create'
import Access from './pages/Access'

function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches
    || (window.navigator as Navigator & { standalone?: boolean }).standalone === true
}

function MagicLinkHandler({ children }: { children: React.ReactNode }) {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showOpenApp, setShowOpenApp] = useState(false)
  const [verifyError, setVerifyError] = useState(false)

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
        if (isStandalone()) {
          // Already inside the PWA — navigate in-place
          navigate('/', { replace: true })
        } else {
          // Opened in a browser tab (email client, etc.) — prompt to open the app
          setShowOpenApp(true)
        }
      })
      .catch(() => setVerifyError(true))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (verifyError) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>❌</div>
        <h2 style={{ marginBottom: '0.5rem' }}>Link expired</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>This magic link has expired or already been used.</p>
        <button className="btn btn-primary" onClick={() => window.open('/app/', '_self')}>
          Back to Trufo
        </button>
      </div>
    )
  }

  if (showOpenApp) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
        <h2 style={{ marginBottom: '0.5rem' }}>You're signed in!</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Tap below to open Trufo.</p>
        <button className="btn btn-primary" onClick={() => window.open('/app/', '_self')}>
          Open Trufo App
        </button>
      </div>
    )
  }

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
