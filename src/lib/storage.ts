import { v4 as uuidv4 } from 'uuid'
import { TrufoObject, CreateObjectData } from '../types'
import { User } from './auth'

const STORAGE_KEY = 'trufo_objects'

// Generate a random token
function generateToken(): string {
  return uuidv4().replace(/-/g, '')
}

// Get all objects from localStorage
export function getAllObjects(): TrufoObject[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  } catch (error) {
    console.error('Error loading objects from localStorage:', error)
    return []
  }
}

// Save objects to localStorage
function saveObjects(objects: TrufoObject[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(objects))
  } catch (error) {
    console.error('Error saving objects to localStorage:', error)
  }
}

// Create a new object
export function createObject(data: CreateObjectData, owner: User): TrufoObject {
  const objects = getAllObjects()

  // Check if name already exists
  if (objects.some(obj => obj.name === data.name)) {
    throw new Error('Object with this name already exists')
  }

  const now = Date.now()
  const ttl = now + (data.ttlHours * 60 * 60 * 1000)

  const newObject: TrufoObject = {
    id: uuidv4(),
    name: data.name,
    type: data.type,
    content: data.content,
    token: generateToken(),
    ttl,
    createdAt: now,
    hitCount: 0,
    ownerEmail: owner.email,
    ownerName: owner.name
  }

  objects.push(newObject)
  saveObjects(objects)

  return newObject
}

// Get object by name and token
export function getObject(name: string, token: string): TrufoObject | null {
  const objects = getAllObjects()
  const obj = objects.find(o => o.name === name && o.token === token)

  if (!obj) return null

  // Check if expired
  if (obj.ttl < Date.now()) {
    return null
  }

  // Update hit count
  obj.hitCount++
  obj.lastHit = Date.now()

  // For toggle objects, flip the value
  if (obj.type === 'toggle') {
    obj.content = !obj.content
  }

  saveObjects(objects)
  return obj
}

// Update an object
export function updateObject(id: string, updates: Partial<TrufoObject>): TrufoObject | null {
  const objects = getAllObjects()
  const index = objects.findIndex(obj => obj.id === id)

  if (index === -1) return null

  objects[index] = { ...objects[index], ...updates }
  saveObjects(objects)

  return objects[index]
}

// Delete an object
export function deleteObject(id: string): boolean {
  const objects = getAllObjects()
  const filteredObjects = objects.filter(obj => obj.id !== id)

  if (filteredObjects.length === objects.length) return false

  saveObjects(filteredObjects)
  return true
}

// Get objects for a specific user
export function getUserObjects(userEmail: string): TrufoObject[] {
  return getAllObjects().filter(obj => obj.ownerEmail === userEmail)
}

// Get active objects for a specific user
export function getUserActiveObjects(userEmail: string): TrufoObject[] {
  const now = Date.now()
  return getUserObjects(userEmail).filter(obj => obj.ttl > now)
}

// Get expired objects for a specific user
export function getUserExpiredObjects(userEmail: string): TrufoObject[] {
  const now = Date.now()
  return getUserObjects(userEmail).filter(obj => obj.ttl <= now)
}

// Get active objects (not expired)
export function getActiveObjects(): TrufoObject[] {
  const now = Date.now()
  return getAllObjects().filter(obj => obj.ttl > now)
}

// Get expired objects
export function getExpiredObjects(): TrufoObject[] {
  const now = Date.now()
  return getAllObjects().filter(obj => obj.ttl <= now)
}

// Clean up expired objects
export function cleanupExpiredObjects(): number {
  const objects = getAllObjects()
  const now = Date.now()
  const activeObjects = objects.filter(obj => obj.ttl > now)
  const removedCount = objects.length - activeObjects.length

  if (removedCount > 0) {
    saveObjects(activeObjects)
  }

  return removedCount
}

// Get statistics
export function getStats() {
  const objects = getAllObjects()
  const now = Date.now()
  const active = objects.filter(obj => obj.ttl > now)
  const expired = objects.filter(obj => obj.ttl <= now)
  const totalHits = objects.reduce((sum, obj) => sum + obj.hitCount, 0)

  return {
    total: objects.length,
    active: active.length,
    expired: expired.length,
    totalHits
  }
}