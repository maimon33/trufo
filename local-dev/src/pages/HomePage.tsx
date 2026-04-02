import { Link } from 'react-router-dom'
import Layout from '../components/Layout'

export default function HomePage() {
  return (
    <Layout title="Welcome to Trufo">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <p className="text-xl text-gray-600">
            Encrypted object storage with TTL management and MFA protection
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-6 mb-16">
          <div className="md:col-span-3 bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">Create an Object</h2>
            <p className="text-gray-600 mb-6">
              Store a string, boolean, or toggle value — encrypted, with an optional expiry and MFA protection. Get a shareable token when you're done.
            </p>
            <Link
              to="/create"
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
            >
              Get Started
            </Link>
          </div>

          <div className="md:col-span-2 bg-white rounded-lg shadow p-8 flex flex-col justify-center">
            <h2 className="text-xl font-bold text-gray-900 mb-3">My Objects</h2>
            <p className="text-gray-600 mb-6">
              View and manage everything you've stored.
            </p>
            <Link
              to="/manage"
              className="inline-block bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium py-2 px-6 rounded-md transition-colors w-fit"
            >
              Manage
            </Link>
          </div>
        </div>

        <div className="mb-16">
          <h2 className="text-xl font-semibold text-gray-900 mb-8 text-center">How it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold">1</span>
              </div>
              <h3 className="font-semibold mb-1">Create</h3>
              <p className="text-gray-500 text-sm">
                Pick a type, set your content, choose an expiry and optional MFA.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold">2</span>
              </div>
              <h3 className="font-semibold mb-1">Share</h3>
              <p className="text-gray-500 text-sm">
                You get a unique token — share the access URL with whoever needs it.
              </p>
            </div>
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-12 h-12 flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 font-bold">3</span>
              </div>
              <h3 className="font-semibold mb-1">Access</h3>
              <p className="text-gray-500 text-sm">
                Hit the URL — content is decrypted on the fly. One-time or repeatable.
              </p>
            </div>
          </div>
        </div>

        <div className="mb-16 bg-gray-100 rounded-lg p-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 text-center">API</h2>
          <p className="text-gray-500 text-sm mb-4 text-center">Access objects programmatically:</p>
          <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-100 overflow-x-auto">
            <div className="mb-2">
              <span className="text-green-400">GET</span> /access/[name]?token=[token]&amp;totpCode=[123456]
            </div>
            <div>
              <span className="text-yellow-400">POST</span> /api/toggle (flip a boolean)
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-gray-200 text-center text-sm text-gray-400 space-y-3">
          <p>
            Data is encrypted but <strong>not guaranteed to persist</strong>. Don't store secrets, passwords, or API keys.
          </p>
          <div className="flex justify-center gap-6">
            <a
              href="https://github.com/maimon33/trufo"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-600 transition-colors"
            >
              Source
            </a>
            <a
              href="https://www.maimons.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-gray-600 transition-colors"
            >
              maimons.dev
            </a>
          </div>
        </div>
      </div>
    </Layout>
  )
}
