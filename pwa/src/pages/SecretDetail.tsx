import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Layout from '../components/Layout'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { Secret } from '../types'

export default function SecretDetail() {
  const { token } = useParams<{ token: string }>()
  const { auth } = useAuth()
  const navigate = useNavigate()
  const [secret, setSecret] = useState<Secret | null>(null)
  const [content, setContent] = useState<string | boolean>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [codes, setCodes] = useState<string[] | null>(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    if (!auth || !token) return
    setLoading(true); setError('')
    try {
      const listed = await api.listSecrets(auth.email, auth.session)
      const found = listed.secrets.find(item => item.token === token)
      if (!found) { setError('Secret not found or has expired'); return }
      setSecret(found)
      const result = await api.getObjectContent(auth.email, auth.session, found.s3_key)
      setContent(result.content)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load secret')
    } finally { setLoading(false) }
  }, [auth, token])

  useEffect(() => { load() }, [load])

  const copy = async (value: string, message: string) => {
    await navigator.clipboard.writeText(value)
    setNotice(message)
    window.setTimeout(() => setNotice(''), 2000)
  }

  const save = async () => {
    if (!auth || !secret) return
    setSaving(true); setError('')
    try {
      await api.updateObject(auth.email, auth.session, secret.s3_key, content)
      setNotice('Content saved')
    } catch (err) { setError(err instanceof Error ? err.message : 'Save failed') }
    finally { setSaving(false) }
  }

  const regenerate = async () => {
    if (!auth || !secret || !confirm('Regenerate backup codes? Existing codes stop working immediately.')) return
    try { setCodes((await api.regenerateRecoveryCodes(auth.email, auth.session, secret.s3_key)).recoveryCodes) }
    catch (err) { setError(err instanceof Error ? err.message : 'Could not regenerate codes') }
  }

  return <Layout title="Manage Secret" action={<button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>Done</button>}>
    {loading && <div className="loading"><div className="spinner" />Loading…</div>}
    {error && <div className="alert alert-error">{error}</div>}
    {notice && <div className="alert alert-success">{notice}</div>}
    {secret && !loading && <>
      <div className="card">
        <div className="form-label">Name</div><div style={{ fontWeight: 700, marginBottom: '0.8rem' }}>{secret.name}</div>
        <div className="form-label">Share link</div>
        <div className="copy-row"><span className="value">{secret.access_url}</span><button className="btn btn-secondary btn-sm" onClick={() => copy(secret.access_url, 'Share link copied')}>Copy</button></div>
      </div>
      <div className="card">
        <div className="form-label">Secret content</div>
        {secret.type === 'string' ? <textarea className="input" rows={7} value={content as string} onChange={e => setContent(e.target.value)} /> :
          <div style={{ display: 'flex', gap: '0.5rem' }}><button className={`ttl-btn${content === true ? ' selected' : ''}`} style={{ flex: 1 }} onClick={() => setContent(true)}>True</button><button className={`ttl-btn${content === false ? ' selected' : ''}`} style={{ flex: 1 }} onClick={() => setContent(false)}>False</button></div>}
        <button className="btn btn-primary" style={{ marginTop: '0.75rem' }} onClick={save} disabled={saving || (secret.type === 'string' && !(content as string).trim())}>{saving ? 'Saving…' : 'Save content'}</button>
      </div>
      <div className="card">
        <div className="form-label">Security</div>
        <div style={{ marginBottom: '0.75rem' }}>{secret.security === 'totp' ? 'TOTP required' : secret.security === 'basic' ? 'Email access alert' : 'Link access'}</div>
        {secret.security === 'totp' && secret.totp_secret && <>
          <div className="form-label">Authenticator setup key</div>
          <div className="copy-row"><span className="value">{secret.totp_secret}</span><button className="btn btn-secondary btn-sm" onClick={() => copy(secret.totp_secret!, 'Setup key copied')}>Copy</button></div>
          <button className="btn btn-secondary" style={{ marginTop: '0.75rem' }} onClick={regenerate}>Regenerate backup codes</button>
          {codes && <div className="alert alert-info" style={{ marginTop: '0.75rem', marginBottom: 0 }}><strong>Save these new codes now.</strong><br />{codes.join('\n')}</div>}
        </>}
      </div>
      <div className="card"><div className="form-label">Access</div><div>{secret.access_count} views · expires {new Date(secret.ttl).toLocaleString()}</div></div>
    </>}
  </Layout>
}
