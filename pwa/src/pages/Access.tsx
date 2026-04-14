import { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { api } from '../lib/api'
import type { AccessResult } from '../types'

export default function Access() {
  const { token } = useParams<{ token: string }>()
  const [searchParams] = useSearchParams()
  const secret = searchParams.get('secret') || undefined

  const [result, setResult] = useState<AccessResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [needsTotp, setNeedsTotp] = useState(false)
  const [totpCode, setTotpCode] = useState('')
  const [copied, setCopied] = useState(false)

  const load = async (totp?: string) => {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const res = await api.accessObject(token, secret, totp)
      if (res.requiresTOTP && res.content === null) {
        setNeedsTotp(true)
        setLoading(false)
        return
      }
      setResult(res)
      setNeedsTotp(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load secret')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [token]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleCopy = async () => {
    if (!result?.content) return
    await navigator.clipboard.writeText(String(result.content))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleShare = async () => {
    if (!result?.content) return
    if ('share' in navigator) {
      await navigator.share({ text: String(result.content) })
    } else {
      handleCopy()
    }
  }

  return (
    <div style={{ minHeight: '100dvh', background: 'var(--gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1.5rem' }}>
      <div style={{ background: 'white', borderRadius: 20, padding: '2rem 1.5rem', width: '100%', maxWidth: 400, boxShadow: '0 20px 60px rgba(0,0,0,0.18)' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
          <div style={{ fontSize: '2rem' }}>🔒</div>
          <h2 style={{ fontWeight: 800, fontSize: '1.2rem', marginTop: '0.25rem' }}>Trufo Secret</h2>
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner" />
            Loading…
          </div>
        )}

        {error && !loading && (
          <div className="alert alert-error">{error}</div>
        )}

        {needsTotp && !loading && (
          <form onSubmit={e => { e.preventDefault(); load(totpCode) }}>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1rem', textAlign: 'center' }}>
              This secret requires TOTP verification.
            </p>
            <div className="form-group">
              <input
                className="input input-otp"
                placeholder="000000"
                value={totpCode}
                onChange={e => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                inputMode="numeric"
                autoComplete="one-time-code"
                autoFocus
                maxLength={6}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={totpCode.length !== 6}
            >
              Verify
            </button>
          </form>
        )}

        {result && !loading && (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <div className="form-label" style={{ marginBottom: '0.5rem' }}>Content</div>
              {result.type === 'string' ? (
                <div className="content-value">{String(result.content)}</div>
              ) : (
                <div className={`bool-display ${result.content ? 'bool-true' : 'bool-false'}`}>
                  {result.content ? 'TRUE' : 'FALSE'}
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button className="btn btn-secondary" style={{ flex: 1 }} onClick={handleCopy}>
                {copied ? '✓ Copied' : 'Copy'}
              </button>
              {'share' in navigator && (
                <button className="btn btn-primary" style={{ flex: 1 }} onClick={handleShare}>
                  ↗ Share
                </button>
              )}
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
              {result.hits} view{result.hits !== 1 ? 's' : ''}
              {result.type !== 'string' && ` · ${result.type}`}
            </div>
          </>
        )}

        <div style={{ marginTop: '1.25rem', textAlign: 'center' }}>
          <Link to="/" style={{ fontSize: '0.82rem', color: 'var(--primary)', textDecoration: 'none' }}>
            Open Trufo App →
          </Link>
        </div>
      </div>
    </div>
  )
}
