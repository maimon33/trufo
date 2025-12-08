export type ObjectType = 'string' | 'toggle'

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
}

export interface CreateObjectData {
  name: string
  type: ObjectType
  content: string | boolean
  ttlHours: number
}