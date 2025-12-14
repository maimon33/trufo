import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import Layout from '../components/Layout'
import { accessObject, accessObjectByToken } from '../lib/api-storage'
import { TrufoObject } from '../types'

export default function AccessPage() {
  const { name, token: urlToken } = useParams<{ name?: string; token?: string }>()
  const [searchParams] = useSearchParams()
  const queryToken = searchParams.get('token')
  const secret = searchParams.get('secret')
  const token = urlToken || queryToken // Use URL token if available, otherwise query token

  const [object, setObject] = useState<TrufoObject | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!token || !secret) {
      setError('Missing access token or secret')
      setLoading(false)
      return
    }

    const fetchObject = async () => {
      try {
        let result
        if (name) {
          // Legacy name+token access (now with secret)
          result = await accessObject(name, token, undefined, secret)
        } else {
          // New token-only access (with secret)
          result = await accessObjectByToken(token, undefined, secret)
        }

        if (!result) {
          setError('Object not found or expired')
        } else {
          // Create object for display
          const obj: TrufoObject = {
            id: result.name || token,
            name: result.name || 'Unnamed',
            type: result.type as any || 'string',
            content: result.content,
            token,
            ttl: Date.now() + 86400000, // Mock TTL
            ownerEmail: 'unknown',
            ownerName: 'Unknown',
            hitCount: result.hits,
            lastHit: Date.now(),
            createdAt: Date.now()
          }
          setObject(obj)
        }
      } catch (err) {
        setError('Error accessing object')
      } finally {
        setLoading(false)
      }
    }

    fetchObject()
  }, [name, token])

  if (loading) {
    return (
      <Layout title="Accessing Object">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout title="Access Error">
        <div className="max-w-md mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-md p-6 text-center">
            <div className="text-red-600 text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-semibold text-red-800 mb-2">Access Denied</h2>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </Layout>
    )
  }

  if (!object) {
    return (
      <Layout title="Object Not Found">
        <div className="max-w-md mx-auto">
          <div className="bg-gray-50 border border-gray-200 rounded-md p-6 text-center">
            <div className="text-gray-400 text-4xl mb-4">❓</div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Object Not Found</h2>
            <p className="text-gray-600">The requested object does not exist or has expired.</p>
          </div>
        </div>
      </Layout>
    )
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  return (
    <Layout title="Object Access">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow-lg rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">{object.name}</h2>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                object.type === 'string'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-green-100 text-green-800'
              }`}>
                {object.type}
              </span>
              {object.type === 'toggle' && (
                <span className="text-sm text-gray-500">(Value toggled!)</span>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Content:</label>
              <div className="bg-gray-50 rounded-md p-4">
                <div className="flex items-center justify-between">
                  <pre className="text-gray-900 whitespace-pre-wrap flex-1">
                    {String(object.content)}
                  </pre>
                  <button
                    onClick={() => copyToClipboard(String(object.content))}
                    className="ml-4 px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded transition-colors"
                  >
                    Copy
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Hit Count:</label>
                <p className="text-gray-900 font-mono">{object.hitCount}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Last Access:</label>
                <p className="text-gray-900 text-sm">
                  {object.lastHit ? new Date(object.lastHit).toLocaleString() : 'Never'}
                </p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Expires:</label>
              <p className="text-gray-900 text-sm">{new Date(object.ttl).toLocaleString()}</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Created:</label>
              <p className="text-gray-900 text-sm">{new Date(object.createdAt).toLocaleString()}</p>
            </div>
          </div>

          {object.type === 'toggle' && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <h3 className="text-sm font-medium text-yellow-800 mb-2">Toggle Object Behavior</h3>
              <p className="text-yellow-700 text-sm">
                This object switches between true and false each time it's accessed.
                The value shown above is the current state after this access.
              </p>
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <div className="bg-gray-100 rounded-lg p-4 text-sm text-gray-600">
            <p className="font-medium mb-2">API Response Format:</p>
            <div className="bg-gray-900 text-gray-100 rounded p-3 font-mono text-left">
              {JSON.stringify({
                name: object.name,
                type: object.type,
                content: object.content,
                hitCount: object.hitCount,
                expires: new Date(object.ttl).toISOString()
              }, null, 2)}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}