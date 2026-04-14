import type { Secret, CreateResult, AccessResult } from '../types'

const API_BASE = import.meta.env.VITE_API_URL || ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
  return data as T
}

export const api = {
  sendOTP: (email: string) =>
    request<{ success: boolean }>('/api/validate-email', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),

  verifyOTP: (email: string, code: string) =>
    request<{ verified: boolean; userSecret: string }>('/api/verify-code', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    }),

  sendMagicLink: (email: string, returnUrl: string) =>
    request<{ success: boolean }>('/api/send-magic-link', {
      method: 'POST',
      body: JSON.stringify({ email, returnUrl }),
    }),

  verifyMagicLink: (token: string) =>
    request<{ success: boolean; email: string; userSecret: string }>('/api/verify-magic-link', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),

  listSecrets: (email: string, secret: string) =>
    request<{ secrets: Secret[]; total: number }>('/api/list-secrets', {
      method: 'POST',
      body: JSON.stringify({ email, secret }),
    }),

  createObject: (data: {
    name: string
    type: string
    content: string | boolean
    ttlHours: number
    ownerEmail: string
    ownerName: string
    securityType: string
    oneTimeAccess: boolean
  }) =>
    request<{
      success: boolean
      object: CreateResult
      userSecret: string
      security?: { totpSecret: string; totpQR: string; recoveryCodes: string[] }
    }>('/api/objects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  accessObject: (token: string, secret?: string, totpCode?: string) => {
    const params = new URLSearchParams({ token })
    if (secret) params.set('secret', secret)
    if (totpCode) params.set('totpCode', totpCode)
    return request<AccessResult>(`/api/objects?${params}`)
  },

  deleteObject: (email: string, secret: string, objectId: string, s3Key: string) =>
    request<{ success: boolean }>('/api/delete-object', {
      method: 'POST',
      body: JSON.stringify({ email, secret, objectId, s3Key }),
    }),
}
