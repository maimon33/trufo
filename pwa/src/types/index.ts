export type ObjectType = 'string' | 'boolean' | 'toggle'
export type SecurityType = 'none' | 'basic' | 'totp'

export interface Secret {
  token: string
  access_secret: string
  type: ObjectType
  security: SecurityType
  ttl: number         // unix ms
  preview: string
  created: number     // unix ms
  one_time: boolean
  access_count: number
  access_url: string
  s3_key: string
}

export interface CreateResult {
  token: string
  accessSecret: string
  name: string
  type: ObjectType
  securityType: SecurityType
  oneTimeAccess: boolean
  ttl: number
  createdAt: number
}

export interface AccessResult {
  name: string
  type: ObjectType
  content: string | boolean | null
  hits: number
  requiresTOTP?: boolean
  totpQR?: string
}
