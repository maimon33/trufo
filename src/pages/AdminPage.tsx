import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import SignInPrompt from '../components/SignInPrompt'
import { useAuth } from '../components/AuthProvider'
import { adminGetAllObjects, updateObject, deleteObject, adminCleanupExpired } from '../lib/api-storage'
import { checkAdminAccess, authenticateAdmin, clearAdminToken, AdminAuth } from '../lib/admin'
import { TrufoObject } from '../types'

export default function AdminPage() {
  const { user } = useAuth()
  const [objects, setObjects] = useState<TrufoObject[]>([])
  const [filter, setFilter] = useState<'all' | 'active' | 'expired'>('all')
  const [editingObject, setEditingObject] = useState<TrufoObject | null>(null)
  const [editContent, setEditContent] = useState('')
  const [adminAuth, setAdminAuth] = useState<AdminAuth>({ isAdmin: false, token: null })
  const [adminToken, setAdminToken] = useState('')
  const [isCheckingAuth, setIsCheckingAuth] = useState(true)
  const [isAuthenticating, setIsAuthenticating] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      setIsCheckingAuth(true)
      const auth = await checkAdminAccess()
      setAdminAuth(auth)
      setIsCheckingAuth(false)
    }

    if (user) {
      checkAuth()
    } else {
      setIsCheckingAuth(false)
    }
  }, [user])

  const loadObjects = async () => {
    if (!adminAuth.token) return

    const allObjects = await adminGetAllObjects(adminAuth.token)
    const now = Date.now()

    let filteredObjects = allObjects
    if (filter === 'active') {
      filteredObjects = allObjects.filter(obj => obj.ttl > now)
    } else if (filter === 'expired') {
      filteredObjects = allObjects.filter(obj => obj.ttl <= now)
    }

    setObjects(filteredObjects)
  }

  useEffect(() => {
    if (adminAuth.isAdmin) {
      loadObjects()
    }
  }, [filter, adminAuth.isAdmin])

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsAuthenticating(true)

    try {
      const success = await authenticateAdmin(adminToken)
      if (success) {
        setAdminAuth({ isAdmin: true, token: adminToken })
        setAdminToken('')
      } else {
        alert('Invalid admin token')
      }
    } catch (error) {
      console.error('Admin authentication failed:', error)
      alert('Authentication failed')
    } finally {
      setIsAuthenticating(false)
    }
  }

  const handleAdminLogout = () => {
    clearAdminToken()
    setAdminAuth({ isAdmin: false, token: null })
  }

  const handleCleanup = async () => {
    if (!adminAuth.token) return

    const result = await adminCleanupExpired(adminAuth.token)
    if (result.success && result.count > 0) {
      loadObjects()
      alert(result.message || `Cleaned up ${result.count} expired objects`)
    } else {
      alert('No expired objects to clean up')
    }
  }

  const handleEdit = (obj: TrufoObject) => {
    setEditingObject(obj)
    setEditContent(String(obj.content))
  }

  const handleSaveEdit = () => {
    if (!editingObject) return

    const newContent = editingObject.type === 'toggle'
      ? editContent === 'true'
      : editContent

    const updated = updateObject(editingObject.id, { content: newContent })
    if (updated) {
      setEditingObject(null)
      setEditContent('')
      loadObjects()
    }
  }

  const handleDelete = (obj: TrufoObject) => {
    if (confirm(`Are you sure you want to delete object "${obj.name}" by ${obj.ownerName}?`)) {
      if (deleteObject(obj.id)) {
        loadObjects()
      }
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const generateAccessUrl = (name: string, token: string) => {
    return `${window.location.origin}/access/${encodeURIComponent(name)}?token=${token}`
  }

  const getStatusBadge = (obj: TrufoObject) => {
    if (obj.ttl <= Date.now()) {
      return <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">Expired</span>
    }
    return <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Active</span>
  }

  if (!user) {
    return (
      <Layout title="Admin Dashboard">
        <SignInPrompt message="Sign in with Google to access admin features." />
      </Layout>
    )
  }

  if (isCheckingAuth) {
    return (
      <Layout title="Admin Dashboard">
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    )
  }

  if (!adminAuth.isAdmin) {
    return (
      <Layout title="Admin Dashboard">
        <div className="max-w-md mx-auto">
          <div className="bg-white shadow-lg rounded-lg p-6">
            <div className="text-center mb-6">
              <div className="text-4xl mb-4">👨‍💼</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Admin Access Required</h2>
              <p className="text-gray-600">Enter the admin token to access the dashboard.</p>
            </div>

            <form onSubmit={handleAdminLogin} className="space-y-4">
              <div>
                <label htmlFor="adminToken" className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Token
                </label>
                <input
                  type="password"
                  id="adminToken"
                  value={adminToken}
                  onChange={(e) => setAdminToken(e.target.value)}
                  required
                  placeholder="Enter admin token"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isAuthenticating || !adminToken.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md transition-colors"
              >
                {isAuthenticating ? 'Verifying...' : 'Access Admin Dashboard'}
              </button>
            </form>

            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <h3 className="text-sm font-medium text-gray-800 mb-2">Admin Token Setup</h3>
              <p className="text-xs text-gray-600">
                The admin token is stored in your S3 bucket at: <br />
                <code className="bg-white px-1 rounded text-xs">/admin/admin-token.txt</code>
              </p>
              <p className="text-xs text-gray-600 mt-2">
                Upload a file with your secret token to this path to enable admin access.
              </p>
            </div>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout title="Admin Dashboard">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                filter === 'all'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All Objects ({objects.length})
            </button>
            <button
              onClick={() => setFilter('active')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                filter === 'active'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setFilter('expired')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                filter === 'expired'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Expired
            </button>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={handleCleanup}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors"
            >
              Cleanup Expired
            </button>
            <button
              onClick={handleAdminLogout}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-md transition-colors"
            >
              Logout Admin
            </button>
          </div>
        </div>

        {objects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No objects found</p>
            <p className="text-gray-400 mt-2">
              {filter === 'active' && 'No active objects exist.'}
              {filter === 'expired' && 'No expired objects exist.'}
              {filter === 'all' && 'No objects have been created yet.'}
            </p>
          </div>
        ) : (
          <div className="bg-white shadow-lg rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Object
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Owner
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type & Content
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Analytics
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {objects.map((obj) => (
                    <tr key={obj.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{obj.name}</div>
                          <div className="text-xs text-gray-500 font-mono truncate max-w-xs">
                            Token: {obj.token.substring(0, 16)}...
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{obj.ownerName}</div>
                          <div className="text-xs text-gray-500">{obj.ownerEmail}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-xs text-gray-500 capitalize mb-1">{obj.type}</div>
                          <div className="text-sm text-gray-900 max-w-xs truncate">
                            {String(obj.content)}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          {getStatusBadge(obj)}
                          <div className="text-xs text-gray-500 mt-1">
                            Expires: {new Date(obj.ttl).toLocaleDateString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <div className="text-gray-900">{obj.hitCount} hits</div>
                          {obj.lastHit && (
                            <div className="text-xs text-gray-500">
                              Last: {new Date(obj.lastHit).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col space-y-1">
                          <div className="flex space-x-1">
                            <button
                              onClick={() => copyToClipboard(obj.token)}
                              className="text-xs bg-blue-500 hover:bg-blue-600 text-white px-2 py-1 rounded transition-colors"
                              title="Copy token"
                            >
                              Token
                            </button>
                            <button
                              onClick={() => copyToClipboard(generateAccessUrl(obj.name, obj.token))}
                              className="text-xs bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded transition-colors"
                              title="Copy access URL"
                            >
                              URL
                            </button>
                          </div>
                          <div className="flex space-x-1">
                            <button
                              onClick={() => handleEdit(obj)}
                              className="text-xs bg-yellow-500 hover:bg-yellow-600 text-white px-2 py-1 rounded transition-colors"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(obj)}
                              className="text-xs bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded transition-colors"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {editingObject && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full">
              <h3 className="text-lg font-semibold mb-4">
                Edit Object: {editingObject.name}
                <span className="text-sm font-normal text-gray-600 ml-2">
                  by {editingObject.ownerName}
                </span>
              </h3>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content ({editingObject.type})
                </label>
                {editingObject.type === 'string' ? (
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <select
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="true">True</option>
                    <option value="false">False</option>
                  </select>
                )}
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleSaveEdit}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={() => {
                    setEditingObject(null)
                    setEditContent('')
                  }}
                  className="flex-1 bg-gray-500 hover:bg-gray-600 text-white py-2 px-4 rounded-md transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}