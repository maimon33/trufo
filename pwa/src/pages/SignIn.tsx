import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'

type Mode = 'magic' | 'otp'
type Step = 'email' | 'sent' | 'code'

export default function SignIn() {
  const { signIn } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<Mode>('otp')
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setError('')
    setLoading(true)

    try {
      if (mode === 'magic') {
        const returnUrl = `${window.location.origin}/app/`
        await api.sendMagicLink(email.trim().toLowerCase(), returnUrl)
        setStep('sent')
      } else {
        await api.sendOTP(email.trim().toLowerCase())
        setStep('code')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (code.length !== 6) return
    setError('')
    setLoading(true)

    try {
      const res = await api.verifyOTP(email.trim().toLowerCase(), code)
      if (res.verified) {
        signIn({ email: res.email, session: res.session })
        navigate('/', { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="signin-container">
      <div className="signin-card">
        <div className="signin-logo">🔒</div>
        <h1 className="signin-title">Trufo</h1>
        <p className="signin-subtitle">Secure secret sharing</p>

        {step === 'email' && (
          <>
            <div className="method-tabs">
              <button
                className={`method-tab${mode === 'otp' ? ' active' : ''}`}
                onClick={() => setMode('otp')}
              >
                🔢 Email Code
              </button>
              <button
                className={`method-tab${mode === 'magic' ? ' active' : ''}`}
                onClick={() => setMode('magic')}
              >
                ✨ Magic Link
              </button>
            </div>

            <form onSubmit={handleEmailSubmit}>
              <div className="form-group">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  autoFocus
                  autoComplete="email"
                  inputMode="email"
                  required
                />
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading
                  ? 'Sending…'
                  : mode === 'magic'
                    ? '✨ Send Magic Link'
                    : '🔢 Send Code'}
              </button>
            </form>
          </>
        )}

        {step === 'sent' && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📬</div>
            <p style={{ fontWeight: 700, marginBottom: '0.5rem' }}>Check your email</p>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Tap the magic link in your email to sign in. It expires in 10 minutes.
            </p>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
              After tapping the link, you'll be brought right back to the app.
            </p>
            <button
              className="btn btn-secondary"
              onClick={() => { setStep('email'); setError('') }}
            >
              Back
            </button>
          </div>
        )}

        {step === 'code' && (
          <form onSubmit={handleCodeSubmit}>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              Enter the 6-digit code sent to <strong>{email}</strong>
            </p>

            <div className="form-group">
              <input
                type="text"
                className="input input-otp"
                placeholder="000000"
                value={code}
                onChange={e => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                maxLength={6}
              />
            </div>

            {error && <div className="alert alert-error">{error}</div>}

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || code.length !== 6}
            >
              {loading ? 'Verifying…' : 'Verify Code'}
            </button>

            <button
              type="button"
              className="btn btn-secondary"
              style={{ marginTop: '0.5rem' }}
              onClick={() => { setStep('email'); setCode(''); setError('') }}
            >
              Back
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
