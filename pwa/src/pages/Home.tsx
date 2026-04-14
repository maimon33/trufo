import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { Secret } from '../types'

function formatExpiry(ttlMs: number): { label: string; cls: string } {
  const diff = ttlMs - Date.now()
  if (diff <= 0) return { label: 'Expired', cls: 'expiry expired' }
  const h = Math.floor(diff / 3_600_000)
  const d = Math.floor(h / 24)
  if (d > 1) return { label: `${d}d left`, cls: 'expiry' }
  if (h > 2) return { label: `${h}h left`, cls: 'expiry soon' }
  return { label: `${h}h left`, cls: 'expiry soon' }
}

function TypeBadge({ type }: { type: string }) {
  return <span className={`badge badge-${type}`}>{type}</span>
}

function SecretCard({
  secret,
  onShare,
  onDelete,
}: {
  secret: Secret
  onShare: (s: Secret) => void
  onDelete: (s: Secret) => void
}) {
  const expiry = formatExpiry(secret.ttl)

  return (
    <div className="card">
      <div className="secret-item">
        <div className="secret-meta">
          <div className="secret-name">{secret.token.slice(0, 8)}…</div>
          <div className="secret-preview">{secret.preview || '—'}</div>
          <div className="secret-footer">
            <TypeBadge type={secret.type} />
            {secret.one_time && <span className="badge badge-1time">1×</span>}
            {secret.security === 'totp' && <span className="badge badge-totp">TOTP</span>}
            <span className={expiry.cls}>{expiry.label}</span>
          </div>
        </div>
        <div className="secret-actions">
          <button className="btn btn-secondary btn-sm" onClick={() => onShare(secret)}>
            Share
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => onDelete(secret)}>
            Del
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  const { auth, signOut } = useAuth()
  const navigate = useNavigate()
  const [secrets, setSecrets] = useState<Secret[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!auth) return
    setLoading(true)
    setError('')
    try {
      const res = await api.listSecrets(auth.email, auth.secret)
      setSecrets(res.secrets)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets')
    } finally {
      setLoading(false)
    }
  }, [auth])

  useEffect(() => { load() }, [load])

  const handleShare = async (secret: Secret) => {
    const url = secret.access_url
    if (navigator.share) {
      try {
        await navigator.share({ title: 'Trufo secret', url })
      } catch {
        // dismissed
      }
    } else {
      await navigator.clipboard.writeText(url)
      alert('Link copied to clipboard')
    }
  }

  const handleDelete = async (secret: Secret) => {
    if (!auth) return
    if (!confirm('Delete this secret?')) return
    setDeleting(secret.token)
    try {
      await api.deleteObject(auth.email, auth.secret, secret.token, secret.s3_key)
      setSecrets(prev => prev.filter(s => s.token !== secret.token))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeleting(null)
    }
  }

  const headerAction = (
    <button
      className="btn btn-ghost btn-sm"
      onClick={() => { signOut(); navigate('/signin', { replace: true }) }}
    >
      Sign out
    </button>
  )

  return (
    <Layout title={`My Secrets`} action={headerAction}>
      {loading && (
        <div className="loading">
          <div className="spinner" />
          Loading…
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          {error}
          <button
            style={{ marginLeft: '0.5rem', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
            onClick={load}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && secrets.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🔐</div>
          <p>No secrets yet</p>
          <button className="btn btn-primary" style={{ maxWidth: 200, margin: '0 auto' }} onClick={() => navigate('/create')}>
            Create your first
          </button>
        </div>
      )}

      {secrets.map(secret => (
        <SecretCard
          key={secret.token}
          secret={secret}
          onShare={handleShare}
          onDelete={deleting === secret.token ? () => {} : handleDelete}
        />
      ))}

      {secrets.length > 0 && (
        <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          {secrets.length} secret{secrets.length !== 1 ? 's' : ''} · {auth?.email}
        </p>
      )}
    </Layout>
  )
}
