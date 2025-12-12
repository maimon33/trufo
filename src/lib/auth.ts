export interface User {
  email: string
  name: string
  picture?: string
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

// Load Google Identity Services
export const loadGoogleAuth = (): Promise<void> => {
  return new Promise((resolve) => {
    if (window.google) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.onload = () => resolve()
    document.head.appendChild(script)
  })
}

// Get current user from localStorage
export const getCurrentUser = (): User | null => {
  try {
    const stored = localStorage.getItem('trufo_user')
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

// Set current user in localStorage
export const setCurrentUser = (user: User | null): void => {
  if (user) {
    localStorage.setItem('trufo_user', JSON.stringify(user))
  } else {
    localStorage.removeItem('trufo_user')
  }
}

// Sign in with Google
export const signInWithGoogle = async (): Promise<User | null> => {
  await loadGoogleAuth()

  return new Promise((resolve) => {
    if (!window.google || !GOOGLE_CLIENT_ID) {
      console.error('Google OAuth not configured')
      resolve(null)
      return
    }

    try {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response: any) => {
          try {
            if (!response.credential) {
              console.error('No credential received from Google')
              resolve(null)
              return
            }

            // Decode JWT token (basic parsing, in production use proper JWT library)
            const payload = JSON.parse(atob(response.credential.split('.')[1]))

            const user: User = {
              email: payload.email,
              name: payload.name,
              picture: payload.picture
            }

            setCurrentUser(user)
            resolve(user)
          } catch (error) {
            console.error('Failed to parse Google response:', error)
            resolve(null)
          }
        },
        cancel_on_tap_outside: false
      })

      // Try popup first, fallback to One Tap
      window.google.accounts.id.prompt((notification: any) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          console.log('One Tap not displayed, will use button')
        }
      })

    } catch (error) {
      console.error('Google OAuth initialization failed:', error)
      resolve(null)
    }
  })
}

// Sign out
export const signOut = (): void => {
  setCurrentUser(null)
  if (window.google) {
    window.google.accounts.id.disableAutoSelect()
  }
}


// Declare global types for Google Identity Services
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void
          prompt: (callback?: (notification: any) => void) => void
          renderButton: (parent: HTMLElement, options: any) => void
          disableAutoSelect: () => void
        }
      }
    }
  }
}