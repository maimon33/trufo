import { TrufoObject } from '../types'

// Set this to your Lambda Function URL after deployment
const API_BASE_URL = import.meta.env.VITE_LAMBDA_API_URL || 'https://your-function-url.lambda-url.region.on.aws'

interface ApiResponse<T = any> {
  success?: boolean
  error?: string
  objects?: T[]
  object?: T
  content?: any
  hits?: number
  deletedCount?: number
  message?: string
}

// API request helper
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.error || `HTTP ${response.status}`)
  }

  return response.json()
}

// Create a new object
export async function createObject(object: TrufoObject): Promise<boolean> {
  try {
    await apiRequest<ApiResponse>('/objects', {
      method: 'POST',
      body: JSON.stringify(object),
    })
    return true
  } catch (error) {
    console.error('Failed to create object:', error)
    return false
  }
}

// Get object by name and token (public access)
export async function accessObject(name: string, token: string): Promise<{ content: any; hits: number } | null> {
  try {
    const response = await apiRequest<ApiResponse>(`/objects?name=${encodeURIComponent(name)}&token=${encodeURIComponent(token)}`)
    return {
      content: response.content,
      hits: response.hits || 0
    }
  } catch (error) {
    console.error('Failed to access object:', error)
    return null
  }
}

// Get all objects for a user
export async function getUserObjects(email: string): Promise<TrufoObject[]> {
  try {
    const response = await apiRequest<ApiResponse>(`/user-objects?email=${encodeURIComponent(email)}`)
    const objects = response.objects || []

    // Cache objects in localStorage for offline access
    setStoredObjects(objects)

    return objects
  } catch (error) {
    console.error('Failed to get user objects:', error)
    // Return cached objects if API fails
    return getStoredObjects().filter(obj => obj.ownerEmail === email)
  }
}

// Get active objects for a user
export async function getUserActiveObjects(email: string): Promise<TrufoObject[]> {
  const objects = await getUserObjects(email)
  const now = Date.now()
  return objects.filter(obj => obj.ttl > now)
}

// Get expired objects for a user
export async function getUserExpiredObjects(email: string): Promise<TrufoObject[]> {
  const objects = await getUserObjects(email)
  const now = Date.now()
  return objects.filter(obj => obj.ttl <= now)
}

// Cleanup expired objects for current user
export async function cleanupExpiredObjects(email: string): Promise<number> {
  try {
    const expiredObjects = await getUserExpiredObjects(email)
    let removedCount = 0

    for (const obj of expiredObjects) {
      const success = await deleteObject(obj.id)
      if (success) removedCount++
    }

    return removedCount
  } catch (error) {
    console.error('Failed to cleanup expired objects:', error)
    return 0
  }
}

// Update an object
export async function updateObject(id: string, updates: Partial<TrufoObject>): Promise<TrufoObject | null> {
  try {
    const response = await apiRequest<ApiResponse>('/objects', {
      method: 'PUT',
      body: JSON.stringify({ id, updates }),
    })
    return response.object || null
  } catch (error) {
    console.error('Failed to update object:', error)
    return null
  }
}

// Delete an object
export async function deleteObject(id: string): Promise<boolean> {
  try {
    await apiRequest<ApiResponse>(`/objects?id=${encodeURIComponent(id)}`, {
      method: 'DELETE',
    })
    return true
  } catch (error) {
    console.error('Failed to delete object:', error)
    return false
  }
}

// Admin: Get all objects
export async function adminGetAllObjects(adminToken: string): Promise<TrufoObject[]> {
  try {
    const response = await apiRequest<ApiResponse>(`/admin/objects?adminToken=${encodeURIComponent(adminToken)}`)
    return response.objects || []
  } catch (error) {
    console.error('Failed to get all objects:', error)
    return []
  }
}

// Admin: Cleanup expired objects
export async function adminCleanupExpired(adminToken: string): Promise<{ success: boolean; count: number; message: string }> {
  try {
    const response = await apiRequest<ApiResponse>('/admin/cleanup', {
      method: 'POST',
      body: JSON.stringify({ adminToken }),
    })
    return {
      success: response.success || false,
      count: response.deletedCount || 0,
      message: response.message || ''
    }
  } catch (error) {
    console.error('Failed to cleanup objects:', error)
    return {
      success: false,
      count: 0,
      message: 'Cleanup failed'
    }
  }
}

// Backward compatibility: Keep localStorage functions for caching
export function getStoredObjects(): TrufoObject[] {
  try {
    const stored = localStorage.getItem('trufo_objects')
    return stored ? JSON.parse(stored) : []
  } catch {
    return []
  }
}

export function setStoredObjects(objects: TrufoObject[]): void {
  localStorage.setItem('trufo_objects', JSON.stringify(objects))
}

export function clearStoredObjects(): void {
  localStorage.removeItem('trufo_objects')
}

// Get statistics from stored objects (for homepage)
export function getStats() {
  const objects = getStoredObjects()
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