import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import SignInPrompt from '../components/SignInPrompt'
import { useAuth } from '../components/AuthProvider'
import { getUserObjects, getUserActiveObjects, getUserExpiredObjects, updateObject, deleteObject, cleanupExpiredObjects } from '../lib/api-storage'
import { TrufoObject } from '../types'

export default function ManagePage() {
  const { user } = useAuth()
  const [objects, setObjects] = useState<TrufoObject[]>([])
  const [filter, setFilter] = useState<'all' | 'active' | 'expired'>('all')
  const [editingObject, setEditingObject] = useState<TrufoObject | null>(null)
  const [editContent, setEditContent] = useState('')

  const loadObjects = async () => {
    if (!user) return

    let filteredObjects: TrufoObject[]
    if (filter === 'active') {
      filteredObjects = await getUserActiveObjects(user.email)
    } else if (filter === 'expired') {
      filteredObjects = await getUserExpiredObjects(user.email)
    } else {
      filteredObjects = await getUserObjects(user.email)
    }

    setObjects(filteredObjects)
  }

  useEffect(() => {
    loadObjects()
  }, [filter, user])

  const handleCleanup = async () => {
    if (!user) return

    const removedCount = await cleanupExpiredObjects(user.email)
    if (removedCount > 0) {
      loadObjects()
      alert(`Cleaned up ${removedCount} expired objects`)
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
    if (confirm(`Are you sure you want to delete object "${obj.name}"?`)) {
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
      <Layout title="My Objects">
        <SignInPrompt message="Sign in to view and manage your objects." />
      </Layout>
    )
  }

  return (
    <Layout title="My Objects">
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
              All Objects
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

          <button
            onClick={handleCleanup}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors"
          >
            Cleanup Expired
          </button>
        </div>

        {objects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No objects found</p>
            <p className="text-gray-400 mt-2">
              {filter === 'active' && 'No active objects exist.'}
              {filter === 'expired' && 'No expired objects exist.'}
              {filter === 'all' && 'Create your first object to get started.'}
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
                            Expires: {new Date(obj.ttl).toLocaleString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <div className="text-gray-900">{obj.hitCount} hits</div>
                          {obj.lastHit && (
                            <div className="text-xs text-gray-500">
                              Last: {new Date(obj.lastHit).toLocaleString()}
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
              <h3 className="text-lg font-semibold mb-4">Edit Object: {editingObject.name}</h3>

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