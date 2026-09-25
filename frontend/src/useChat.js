import { useCallback, useEffect, useState } from 'react'
import { buildMetadata, client, describeGrpcError, proto, StatusCode } from './grpcClient.js'

const MAX_RECONNECT_DELAY_MS = 10000

// Server streaming SubscribeChat (réception) + unary SendChatMessage (envoi) :
// gRPC-Web ne supporte pas le streaming bidirectionnel dans le navigateur.
export function useChat() {
  const [messages, setMessages] = useState([])
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  useEffect(() => {
    let stream = null
    let retryTimer = null
    let attempt = 0
    let stopped = false

    const connect = () => {
      retryTimer = null
      setMessages([]) // le serveur renvoie l'historique à chaque abonnement
      stream = client.subscribeChat(new proto.SubscribeChatRequest(), buildMetadata())
      stream.on('metadata', () => {
        attempt = 0
        setConnected(true)
        setError('')
      })
      stream.on('data', (message) => {
        setConnected(true)
        setMessages((current) => [...current, {
          author: message.getAuthor(),
          text: message.getText(),
          sentAt: message.getSentAtMs(),
        }])
      })
      const reconnect = (streamError) => {
        setConnected(false)
        // 'error' puis 'end' peuvent arriver pour le même flux : une seule reconnexion
        if (stopped || retryTimer || streamError?.code === StatusCode.CANCELLED) return
        if (streamError) setError(describeGrpcError(streamError))
        // Backoff exponentiel : 1s, 2s, 4s… jusqu'à 10s
        const delay = Math.min(1000 * 2 ** attempt, MAX_RECONNECT_DELAY_MS)
        attempt += 1
        retryTimer = setTimeout(connect, delay)
      }
      stream.on('error', reconnect)
      stream.on('end', () => reconnect())
    }

    connect()
    return () => {
      stopped = true
      clearTimeout(retryTimer)
      stream?.cancel()
    }
  }, [])

  const send = useCallback((author, text) => {
    const request = new proto.ChatMessage()
    request.setAuthor(author)
    request.setText(text)
    setSending(true)
    client.sendChatMessage(
      request,
      buildMetadata({ timeoutMs: 2000 }),
      (err) => {
        setSending(false)
        if (!err) {
          setError('')
          return
        }
        setError(describeGrpcError(err))
      },
    )
  }, [])

  return { messages, connected, error, sending, send }
}
