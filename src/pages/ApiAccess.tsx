import { useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { accessObject } from '../lib/api-storage'

export default function ApiAccess() {
  const { name } = useParams<{ name: string }>()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  useEffect(() => {
    if (!name || !token) {
      document.body.innerHTML = JSON.stringify({
        error: 'Missing object name or token',
        status: 400
      }, null, 2)
      return
    }

    const fetchObject = async () => {
      try {
        const result = await accessObject(name, token)
        if (!result) {
          document.body.innerHTML = JSON.stringify({
            error: 'Object not found or expired',
            status: 404
          }, null, 2)
          return
        }

        // Return pure JSON response
        const response = {
          name: name,
          content: result.content,
          hitCount: result.hits,
          status: 200
        }

        document.body.innerHTML = JSON.stringify(response, null, 2)

        // Set content type if possible
        try {
          document.contentType = 'application/json'
        } catch {}

      } catch (err) {
        document.body.innerHTML = JSON.stringify({
          error: 'Error accessing object',
          status: 500
        }, null, 2)
      }
    }

    fetchObject()
  }, [name, token])

  return <div>Loading...</div>
}