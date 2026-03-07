export type ObjectType = 'string' | 'boolean' | 'toggle'

export interface TrufoObject {
  id: string
  name: string
  type: ObjectType
  content: string | boolean
  token: string
  ttl: number // timestamp
  createdAt: number // timestamp
  hitCount: number
  lastHit?: number // timestamp
  ownerEmail: string
  ownerName: string
  oneTimeAccess?: boolean // if true, delete after first access
  totpSecret?: string // TOTP secret for MFA
}

export interface CreateObjectData {
  name: string
  type: ObjectType
  content: string | boolean
  ttlHours: number
  oneTimeAccess?: boolean
  enableMFA?: boolean
}