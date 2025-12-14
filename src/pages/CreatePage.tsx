import { useState } from 'react'
import Layout from '../components/Layout'
import SignInPrompt from '../components/SignInPrompt'
import { useAuth } from '../components/AuthProvider'
import { createObject } from '../lib/api-storage'
import { CreateObjectData, TrufoObject, ObjectType } from '../types'

export default function CreatePage() {
  const { user } = useAuth()
  const [formData, setFormData] = useState({
    name: '',
    type: 'string' as ObjectType,
    content: '',
    ttlHours: '24',
    oneTimeAccess: false,
    enableMFA: false
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TrufoObject | null>(null)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      // Validate that boolean/toggle objects have a valid selection
      if ((formData.type === 'boolean' || formData.type === 'toggle') && formData.content === '') {
        throw new Error('Please select a boolean value (true or false)')
      }

      const createData: CreateObjectData & { ownerEmail: string; ownerName: string } = {
        name: formData.name,
        type: formData.type,
        content: formData.type === 'toggle' || formData.type === 'boolean'
          ? formData.content === 'true'
          : formData.content,
        ttlHours: parseFloat(formData.ttlHours),
        oneTimeAccess: formData.oneTimeAccess,
        enableMFA: formData.enableMFA,
        ownerEmail: user!.email,
        ownerName: user!.name
      }

      const result = await createObject(createData)
      if (result && result.object) {
        setResult(result.object)
        setFormData({ name: '', type: 'string', content: '', ttlHours: '24', oneTimeAccess: false, enableMFA: false })
      } else {
        throw new Error('Failed to create object')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => {
      const updated = {
        ...prev,
        [name]: value
      }

      // When switching to boolean/toggle, set a default value if content is empty
      if (name === 'type' && (value === 'boolean' || value === 'toggle') && prev.content === '') {
        updated.content = 'true'
      }
      // When switching to string, clear content if it was a boolean value
      if (name === 'type' && value === 'string' && (prev.content === 'true' || prev.content === 'false')) {
        updated.content = ''
      }

      return updated
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const generateAccessUrl = (token: string, userSecret: string) => {
    return `${window.location.origin}/object/${token}?secret=${userSecret}`
  }

  const generateApiUrl = (token: string, userSecret: string) => {
    return `${window.location.origin}/object/${token}?secret=${userSecret}`
  }

  if (!user) {
    return (
      <Layout title="Create New Object">
        <SignInPrompt message="Sign in to create objects and manage your content." />
      </Layout>
    )
  }

  return (
    <Layout title="Create New Object">
      <div className="max-w-2xl mx-auto">
        {result && (
          <div className="mb-8 p-6 bg-green-50 border border-green-200 rounded-lg">
            <h2 className="text-xl font-semibold text-green-800 mb-4">
              Object Created Successfully!
            </h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Object Name:</label>
                <p className="text-gray-900 font-mono">{result.name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Type:</label>
                <p className="text-gray-900 capitalize">{result.type}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Content:</label>
                <p className="text-gray-900">{String(result.content)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Access Token:</label>
                <div className="flex items-center space-x-2">
                  <p className="text-gray-900 font-mono text-sm flex-1 truncate">{result.token}</p>
                  <button
                    onClick={() => copyToClipboard(result.token)}
                    className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Copy
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Your Access Secret:</label>
                <div className="flex items-center space-x-2">
                  <p className="text-gray-900 font-mono text-sm flex-1 truncate">{(result as any).userSecret}</p>
                  <button
                    onClick={() => copyToClipboard((result as any).userSecret)}
                    className="px-2 py-1 text-xs bg-purple-500 text-white rounded hover:bg-purple-600"
                  >
                    Copy
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  This secret is the same for all your objects. Keep it secure!
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Web Access URL:</label>
                <div className="flex items-center space-x-2">
                  <p className="text-gray-900 font-mono text-sm flex-1 truncate">
                    {generateAccessUrl(result.token, (result as any).userSecret)}
                  </p>
                  <button
                    onClick={() => copyToClipboard(generateAccessUrl(result.token, (result as any).userSecret))}
                    className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Copy
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Access URL for API/Scripts:</label>
                <div className="flex items-center space-x-2">
                  <p className="text-gray-900 font-mono text-sm flex-1 truncate">
                    {generateApiUrl(result.token, (result as any).userSecret)}
                  </p>
                  <button
                    onClick={() => copyToClipboard(generateApiUrl(result.token, (result as any).userSecret))}
                    className="px-2 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    Copy
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Expires At:</label>
                <p className="text-gray-900">{new Date(result.ttl).toLocaleString()}</p>
              </div>
              {result.type === 'boolean' && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-blue-800 text-sm mb-2">
                    <strong>Boolean Object:</strong> This object stores a boolean value. You can toggle it using the API:
                  </p>
                  <div className="bg-gray-800 text-gray-100 p-2 rounded font-mono text-xs">
                    POST {import.meta.env.VITE_LAMBDA_API_URL}/toggle<br/>
                    Body: {JSON.stringify({ name: result.name, token: result.token })}
                  </div>
                </div>
              )}
              {result.type === 'toggle' && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                  <p className="text-yellow-800 text-sm">
                    <strong>Toggle Object:</strong> This object will flip between true/false each time it's accessed via GET.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-lg p-6">
          <div className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Object Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter a unique name for your object"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                This name must be unique across all objects
              </p>
            </div>

            <div>
              <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
                Object Type *
              </label>
              <select
                id="type"
                name="type"
                value={formData.type}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="string">String - Returns text content</option>
                <option value="boolean">Boolean - Returns fixed true/false value</option>
                <option value="toggle">Toggle - Flips true/false on each access</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Toggle objects switch between true and false each time they're accessed
              </p>
            </div>

            <div>
              <label htmlFor="content" className="block text-sm font-medium text-gray-700 mb-2">
                Content *
              </label>
              {formData.type === 'string' ? (
                <textarea
                  id="content"
                  name="content"
                  value={formData.content}
                  onChange={handleChange}
                  required
                  rows={6}
                  placeholder="Enter the content you want to store"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <select
                  id="content"
                  name="content"
                  value={formData.content}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              )}
            </div>

            <div>
              <label htmlFor="ttlHours" className="block text-sm font-medium text-gray-700 mb-2">
                Time to Live (TTL) *
              </label>
              <select
                id="ttlHours"
                name="ttlHours"
                value={formData.ttlHours}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="0.0167">1 minute</option>
                <option value="0.0833">5 minutes</option>
                <option value="1">1 hour</option>
                <option value="6">6 hours</option>
                <option value="24">1 day</option>
                <option value="168">7 days</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                The object will automatically expire after this time
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="oneTimeAccess"
                  name="oneTimeAccess"
                  checked={formData.oneTimeAccess}
                  onChange={(e) => setFormData(prev => ({ ...prev, oneTimeAccess: e.target.checked }))}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="oneTimeAccess" className="ml-2 block text-sm text-gray-700">
                  One-time access
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enableMFA"
                  name="enableMFA"
                  checked={formData.enableMFA}
                  onChange={(e) => setFormData(prev => ({ ...prev, enableMFA: e.target.checked }))}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enableMFA" className="ml-2 block text-sm text-gray-700">
                  Enable TOTP MFA
                </label>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              One-time access deletes the object after first access. MFA requires TOTP verification to view content.
            </p>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-md transition-colors"
            >
              {loading ? 'Creating Object...' : 'Create Object'}
            </button>
          </div>
        </form>

        <div className="mt-8 text-center text-sm text-gray-600">
          <p>
            After creation, you'll receive a unique token that can be used to access your object.
          </p>
          <p>
            Save the token securely - it cannot be recovered once this page is closed.
          </p>
        </div>
      </div>
    </Layout>
  )
}