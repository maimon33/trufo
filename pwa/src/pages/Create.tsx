import { useState } from 'react'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { CreateResult } from '../types'

type ObjectType = 'string' | 'boolean' | 'toggle'
type SecurityType = 'none' | 'basic' | 'totp'

const TTL_OPTIONS = [
  { label: '1h',  hours: 1 },
  { label: '24h', hours: 24 },
  { label: '7d',  hours: 168 },
  { label: '30d', hours: 720 },
]

export default function Create() {
  const { auth } = useAuth()

  const [name, setName] = useState('')
  const [type, setType] = useState<ObjectType>('string')
  const [content, setContent] = useState('')
  const [boolValue, setBoolValue] = useState(true)
  const [ttlHours, setTtlHours] = useState(24)
  const [security, setSecurity] = useState<SecurityType>('none')
  const [oneTime, setOneTime] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<(CreateResult & { accessSecret: string }) | null>(null)
  const [totpInfo, setTotpInfo] = useState<{ secret: string; qr: string; codes: string[] } | null>(null)
  const [copied, setCopied] = useState(false)

  const reset = () => {
    setName(''); setContent(''); setResult(null); setTotpInfo(null)
    setType('string'); setSecurity('none'); setOneTime(false); setTtlHours(24)
    setError(''); setCopied(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!auth) return
    setError('')
    setLoading(true)

    try {
      const actualContent = type === 'string' ? content : boolValue

      const res = await api.createObject({
        name: name.trim(),
        type,
        content: actualContent,
        ttlHours,
        ownerEmail: auth.email,
        ownerName: auth.email,
        securityType: security,
        oneTimeAccess: oneTime,
      })

      setResult(res.object)
      if (res.security) {
        setTotpInfo({
          secret: res.security.totpSecret,
          qr: res.security.totpQR,
          codes: res.security.recoveryCodes,
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create secret')
    } finally {
      setLoading(false)
    }
  }

  const shareUrl = result
    ? `${window.location.origin}/access/${result.token}?secret=${result.accessSecret}`
    : ''

  const handleShare = async () => {
    if (!result) return
    if (navigator.share) {
      try {
        await navigator.share({ title: `Trufo secret: ${result.name}`, url: shareUrl })
      } catch { /* dismissed */ }
    } else {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (result) {
    return (
      <Layout title="Secret Created">
        <div className="result-box">
          <div className="result-label">Name</div>
          <div style={{ fontWeight: 700, marginBottom: '0.75rem' }}>{result.name}</div>

          <div className="result-label">Share Link</div>
          <div className="copy-row" style={{ marginBottom: '0.75rem' }}>
            <span className="value">{shareUrl}</span>
            <button className="btn btn-secondary btn-sm" onClick={handleCopy}>
              {copied ? '✓' : 'Copy'}
            </button>
          </div>

          {result.securityType === 'totp' && totpInfo && (
            <>
              <div className="result-label" style={{ marginTop: '0.75rem' }}>TOTP Secret</div>
              <div className="mono" style={{ marginBottom: '0.5rem' }}>{totpInfo.secret}</div>
              <div className="result-label">Recovery Codes</div>
              <div className="mono" style={{ fontSize: '0.76rem', lineHeight: 1.8 }}>
                {totpInfo.codes.join('\n')}
              </div>
              <div className="alert alert-info" style={{ marginTop: '0.75rem', marginBottom: 0 }}>
                Save these codes — they won't be shown again.
              </div>
            </>
          )}
        </div>

        <button className="btn btn-primary" onClick={handleShare}>
          {'share' in navigator ? '↗ Share' : copied ? '✓ Copied' : 'Copy Link'}
        </button>
        <button className="btn btn-secondary" style={{ marginTop: '0.5rem' }} onClick={reset}>
          Create Another
        </button>
      </Layout>
    )
  }

  return (
    <Layout title="New Secret">
      <form onSubmit={handleSubmit}>
        {/* Name */}
        <div className="form-group">
          <label className="form-label">Name</label>
          <input
            className="input"
            placeholder="e.g. api-key-staging"
            value={name}
            onChange={e => setName(e.target.value)}
            required
            autoComplete="off"
            autoCapitalize="none"
          />
        </div>

        {/* Type */}
        <div className="form-group">
          <label className="form-label">Type</label>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {(['string', 'boolean', 'toggle'] as ObjectType[]).map(t => (
              <button
                key={t}
                type="button"
                className={`ttl-btn${type === t ? ' selected' : ''}`}
                style={{ flex: 1 }}
                onClick={() => setType(t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="form-group">
          <label className="form-label">Content</label>
          {type === 'string' ? (
            <textarea
              className="input"
              placeholder="Enter your secret content…"
              value={content}
              onChange={e => setContent(e.target.value)}
              required
              rows={4}
            />
          ) : (
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className={`ttl-btn${boolValue ? ' selected' : ''}`}
                style={{ flex: 1, color: boolValue ? undefined : undefined }}
                onClick={() => setBoolValue(true)}
              >
                True
              </button>
              <button
                type="button"
                className={`ttl-btn${!boolValue ? ' selected' : ''}`}
                onClick={() => setBoolValue(false)}
              >
                False
              </button>
            </div>
          )}
        </div>

        {/* TTL */}
        <div className="form-group">
          <label className="form-label">Expires after</label>
          <div className="ttl-grid">
            {TTL_OPTIONS.map(opt => (
              <button
                key={opt.hours}
                type="button"
                className={`ttl-btn${ttlHours === opt.hours ? ' selected' : ''}`}
                onClick={() => setTtlHours(opt.hours)}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Options */}
        <div className="card">
          <div className="toggle-row">
            <div>
              <div className="toggle-row-label">One-time access</div>
              <div className="toggle-row-sub">Delete after first view</div>
            </div>
            <label className="toggle">
              <input type="checkbox" checked={oneTime} onChange={e => setOneTime(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
          </div>
          <div className="toggle-row">
            <div>
              <div className="toggle-row-label">Security</div>
              <div className="toggle-row-sub">
                {security === 'none' ? 'None' : security === 'basic' ? 'Email notification on access' : 'TOTP 2FA required'}
              </div>
            </div>
            <select
              className="input"
              style={{ width: 'auto', padding: '0.35rem 0.5rem', fontSize: '0.82rem' }}
              value={security}
              onChange={e => setSecurity(e.target.value as SecurityType)}
            >
              <option value="none">None</option>
              <option value="basic">Email alert</option>
              <option value="totp">TOTP 2FA</option>
            </select>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Creating…' : 'Create Secret'}
        </button>
      </form>
    </Layout>
  )
}
