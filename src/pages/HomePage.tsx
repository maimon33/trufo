import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function HomePage() {
  return (
    <Layout title="Welcome to Trufo">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-xl text-gray-600 mb-8">
            A secure, encrypted object storage system with TTL management and MFA protection
          </p>

          <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-lg max-w-3xl mx-auto">
            <h3 className="text-lg font-semibold text-red-800 mb-3">⚠️ Important Disclaimer</h3>
            <div className="text-red-700 text-sm space-y-2">
              <p><strong>This site takes no responsibility for keeping your data safe.</strong></p>
              <p>• Never store secrets, passwords, API keys, or any sensitive information</p>
              <p>• Site reliability is not promised - data may be lost at any time</p>
              <p>• Use only for temporary, non-critical data</p>
              <p>• Data is encrypted but treat as potentially insecure</p>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create Objects</h2>
            <p className="text-gray-600 mb-6">
              Create string, boolean, or toggle objects with encrypted storage, optional TOTP MFA,
              and configurable TTL. Support for one-time access objects.
            </p>
            <Link
              to="/create"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
            >
              Create Object
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Manage Objects</h2>
            <p className="text-gray-600 mb-6">
              View, edit, and manage all your objects. Monitor access patterns,
              update content, and track usage analytics.
            </p>
            <Link
              to="/manage"
              className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
            >
              Manage Objects
            </Link>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">1</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Create Object</h3>
              <p className="text-gray-600">
                Choose string, boolean, or toggle type. Set content, TTL, and optional MFA protection.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">2</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Get Token</h3>
              <p className="text-gray-600">
                Receive a unique, secure token that grants access to your object.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold text-xl">3</span>
              </div>
              <h3 className="text-lg font-semibold mb-2">Access Content</h3>
              <p className="text-gray-600">
                Use the access URL with token and optional TOTP code. Content is automatically decrypted.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-16 bg-gray-100 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 text-center">API Usage</h2>
          <p className="text-gray-600 mb-6 text-center">
            Access your objects programmatically using simple URLs:
          </p>
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-100 overflow-x-auto">
            <div className="mb-2">
              <span className="text-green-400">GET</span> /access/[object-name]?token=[your-token]&amp;totpCode=[123456]
            </div>
            <div className="mb-2">
              <span className="text-yellow-400">POST</span> /api/toggle (for boolean objects)
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4 text-center">
            TOTP code optional for MFA-enabled objects. Toggle objects flip boolean values. Boolean objects can be toggled via API.
          </p>
        </div>
      </div>
    </Layout>
  )
}