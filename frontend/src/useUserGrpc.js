import { useEffect, useState } from 'react'
import { buildMetadata, client, proto } from './grpcClient.js'

export function useUserGrpc(userId = 1) {
  const [user, setUser] = useState(null)
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [streaming, setStreaming] = useState(true)

  useEffect(() => {
    const metadata = buildMetadata({ timeoutMs: 2000 })
    const request = new proto.GetUserRequest()
    request.setUserId(userId)

    client.getUser(request, metadata, (err, response) => {
      if (err) {
        setError(err.message)
      } else {
        setUser(response?.getUser?.())
      }
      setLoading(false)
    })

    // Liste locale à cet abonnement : pas de doublons si l'effet est relancé (StrictMode)
    const received = []
    const stream = client.listUsers(new proto.ListUsersRequest(), metadata)
    stream.on('data', (streamedUser) => {
      received.push(streamedUser)
      setUsers([...received])
    })
    stream.on('error', (streamError) => {
      // Code 1 = CANCELLED : le flux a été annulé par le démontage du composant
      if (streamError.code !== 1) {
        setError(streamError.message)
      }
      setStreaming(false)
    })
    stream.on('end', () => setStreaming(false))

    return () => stream.cancel()
  }, [userId])

  return { user, users, error, loading, streaming }
}
