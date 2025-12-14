/**
 * Trufo API Storage Library
 *
 * This library provides functions for interacting with the Trufo API backend.
 * All functions use the Lambda Function URL configured via VITE_LAMBDA_API_URL.
 *
 * Features:
 * - Create, read, update, delete objects
 * - Support for string, boolean, and toggle object types
 * - Content encryption/decryption (handled server-side)
 * - TOTP MFA verification for secure objects
 * - Auto-deletion of expired objects
 * - One-time access objects
 * - Boolean object toggling
 *
 * @author Trufo
 * @version 2.0
 */
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
  requiresTOTP?: boolean
  totpQR?: string
  name?: string
  type?: string
}

/**
 * Internal API request helper function
 *
 * @param endpoint - API endpoint path (e.g., '/objects', '/user-objects')
 * @param options - Fetch request options
 * @returns Promise resolving to API response data
 * @throws Error with message from API response or HTTP status
 */
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

/**
 * Create a new object in the Trufo system
 *
 * @param object - Object data including name, type, content, TTL, owner info, and optional flags
 * @returns Promise resolving to API response with created object, or null on failure
 *
 * @example
 * const result = await createObject({
 *   name: 'my-secret',
 *   type: 'string',
 *   content: 'Hello World',
 *   ttlHours: 24,
 *   ownerEmail: 'user@example.com',
 *   ownerName: 'John Doe',
 *   oneTimeAccess: false,
 *   enableMFA: true
 * })
 */
export async function createObject(object: any): Promise<ApiResponse | null> {
  try {
    const response = await apiRequest<ApiResponse>('/objects', {
      method: 'POST',
      body: JSON.stringify(object),
    })
    return response
  } catch (error) {
    console.error('Failed to create object:', error)
    return null
  }
}

/**
 * Access an object by token only (simpler access)
 *
 * @param token - The access token
 * @param totpCode - Optional TOTP code for MFA-enabled objects
 * @returns Promise resolving to object data, or null on failure
 */
export async function accessObjectByToken(token: string, totpCode?: string): Promise<{ name: string; type: string; content: any; hits: number; requiresTOTP?: boolean; totpQR?: string } | null> {
  try {
    const url = `/object?token=${encodeURIComponent(token)}${totpCode ? `&totpCode=${encodeURIComponent(totpCode)}` : ''}`
    const response = await apiRequest<ApiResponse>(url)
    return {
      name: response.name || '',
      type: response.type || 'string',
      content: response.content,
      hits: response.hits || 0,
      requiresTOTP: response.requiresTOTP,
      totpQR: response.totpQR
    }
  } catch (error: any) {
    // Check if error contains TOTP requirement info
    if (error.message.includes('TOTP verification required')) {
      try {
        const url = `/object?token=${encodeURIComponent(token)}`
        const response = await fetch(`${import.meta.env.VITE_LAMBDA_API_URL || 'https://your-function-url.lambda-url.region.on.aws'}${url}`)
        const errorData = await response.json()
        return {
          name: '',
          type: 'string',
          content: null,
          hits: 0,
          requiresTOTP: errorData.requiresTOTP,
          totpQR: errorData.totpQR
        }
      } catch {
        console.error('Failed to access object by token:', error)
        return null
      }
    }
    console.error('Failed to access object by token:', error)
    return null
  }
}

/**
 * Access an object by name and token (public access)
 *
 * @param name - The object name
 * @param token - The access token
 * @param totpCode - Optional TOTP code for MFA-enabled objects
 * @returns Promise resolving to object content and metadata, or null on failure
 *
 * @example
 * // Access a regular object
 * const result = await accessObject('my-object', 'abc123')
 * console.log(result.content) // Object content
 * console.log(result.hits)    // Access count
 *
 * // Access an MFA-enabled object
 * const mfaResult = await accessObject('secure-object', 'def456', '123456')
 * if (mfaResult?.requiresTOTP) {
 *   console.log(mfaResult.totpQR) // QR code for first-time setup
 * }
 */
export async function accessObject(name: string, token: string, totpCode?: string): Promise<{ content: any; hits: number; requiresTOTP?: boolean; totpQR?: string } | null> {
  try {
    const url = `/objects?name=${encodeURIComponent(name)}&token=${encodeURIComponent(token)}${totpCode ? `&totpCode=${encodeURIComponent(totpCode)}` : ''}`
    const response = await apiRequest<ApiResponse>(url)
    return {
      content: response.content,
      hits: response.hits || 0,
      requiresTOTP: response.requiresTOTP,
      totpQR: response.totpQR
    }
  } catch (error: any) {
    // Check if error contains TOTP requirement info
    if (error.message.includes('TOTP verification required')) {
      // Try to extract TOTP info from the error response
      try {
        const url = `/objects?name=${encodeURIComponent(name)}&token=${encodeURIComponent(token)}`
        const response = await fetch(`${import.meta.env.VITE_LAMBDA_API_URL || 'https://your-function-url.lambda-url.region.on.aws'}${url}`)
        const errorData = await response.json()
        return {
          content: null,
          hits: 0,
          requiresTOTP: errorData.requiresTOTP,
          totpQR: errorData.totpQR
        }
      } catch {
        console.error('Failed to access object:', error)
        return null
      }
    }
    console.error('Failed to access object:', error)
    return null
  }
}

/**
 * Get all objects owned by a specific user
 *
 * @param email - The owner's email address
 * @returns Promise resolving to array of user's objects
 *
 * @example
 * const userObjects = await getUserObjects('user@example.com')
 * console.log(`User has ${userObjects.length} objects`)
 */
export async function getUserObjects(email: string): Promise<TrufoObject[]> {
  try {
    const response = await apiRequest<ApiResponse>(`/user-objects?email=${encodeURIComponent(email)}`)
    return response.objects || []
  } catch (error) {
    console.error('Failed to get user objects:', error)
    return []
  }
}

/**
 * Get only active (non-expired) objects for a user
 *
 * @param email - The owner's email address
 * @returns Promise resolving to array of active objects
 */
export async function getUserActiveObjects(email: string): Promise<TrufoObject[]> {
  const objects = await getUserObjects(email)
  const now = Date.now()
  return objects.filter(obj => obj.ttl > now)
}

/**
 * Get only expired objects for a user
 *
 * @param email - The owner's email address
 * @returns Promise resolving to array of expired objects
 */
export async function getUserExpiredObjects(email: string): Promise<TrufoObject[]> {
  const objects = await getUserObjects(email)
  const now = Date.now()
  return objects.filter(obj => obj.ttl <= now)
}

/**
 * Delete all expired objects for a user
 *
 * @param email - The owner's email address
 * @returns Promise resolving to number of objects deleted
 */
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

/**
 * Update an existing object
 *
 * @param id - The object ID
 * @param updates - Partial object data to update
 * @returns Promise resolving to updated object or null on failure
 */
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

/**
 * Delete an object by ID
 *
 * @param id - The object ID
 * @returns Promise resolving to true on success, false on failure
 */
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

/**
 * Toggle a boolean object's value
 * Only works with objects of type 'boolean'
 *
 * @param name - The object name
 * @param token - The access token
 * @returns Promise resolving to new boolean value and hit count, or null on failure
 *
 * @example
 * const result = await toggleBooleanObject('my-flag', 'abc123')
 * if (result) {
 *   console.log(result.content) // true or false
 *   console.log(result.hits)    // Access count
 * }
 */
export async function toggleBooleanObject(name: string, token: string): Promise<{ content: boolean; hits: number } | null> {
  try {
    const response = await apiRequest<ApiResponse>('/toggle', {
      method: 'POST',
      body: JSON.stringify({ name, token }),
    })
    return {
      content: response.content,
      hits: response.hits || 0
    }
  } catch (error) {
    console.error('Failed to toggle boolean object:', error)
    return null
  }
}