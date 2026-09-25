import { useCallback, useState } from 'react'
import { buildMetadata, client, describeGrpcError, proto } from './grpcClient.js'

const STORAGE_KEY = 'grpc-course-session'

function readStoredSession() {
  try {
    const session = JSON.parse(sessionStorage.getItem(STORAGE_KEY))
    return session && session.expiresAt > Date.now() ? session : null
  } catch {
    return null
  }
}

export function useAuth() {
  const [session, setSession] = useState(readStoredSession)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)

  const login = useCallback((username, password) => {
    const request = new proto.LoginRequest()
    request.setUsername(username)
    request.setPassword(password)
    setPending(true)
    setError('')
    client.login(request, buildMetadata({ timeoutMs: 3000 }), (err, response) => {
      setPending(false)
      if (err) {
        setError(describeGrpcError(err))
        return
      }
      const nextSession = { username, token: response.getToken(), expiresAt: response.getExpiresAtMs() }
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession))
      } catch {
        // stockage indisponible (navigation privée) : la session reste en mémoire
      }
      setSession(nextSession)
    })
  }, [])

  const logout = useCallback(() => {
    try {
      sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // rien à nettoyer
    }
    setSession(null)
  }, [])

  return { session, error, pending, login, logout }
}
