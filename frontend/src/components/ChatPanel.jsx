import { useState } from 'react'
import { MessageSquare, Send } from 'lucide-react'
import { Badge } from './ui/badge.jsx'
import { Button } from './ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card.jsx'
import { Separator } from './ui/separator.jsx'
import { useChat } from '../useChat.js'

function formatTime(ms) {
  return ms ? new Date(ms).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''
}

export function ChatPanel() {
  const { messages, connected, error: chatError, sending, send } = useChat()
  const [author, setAuthor] = useState('')
  const [draft, setDraft] = useState('')

  const submit = (event) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text || !author.trim()) return
    send(author.trim(), text)
    setDraft('')
  }

  return (
    <Card className="chat-card">
      <CardHeader>
        <div className="section-heading">
          <div>
            <CardTitle>Chat en direct</CardTitle>
            <CardDescription>Réception : <code>SubscribeChat</code> (server streaming) · Envoi : <code>SendChatMessage</code> (deadline 2 s)</CardDescription>
          </div>
          <Badge variant={connected ? 'secondary' : 'outline'} className={connected ? 'status-badge' : ''}><MessageSquare size={13} /> {connected ? 'Connecté' : 'Reconnexion…'}</Badge>
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="chat-content">
        <ul className="chat-messages" aria-live="polite">
          {messages.length ? messages.map((message, index) => (
            <li key={`${message.sentAt}-${index}`} className={message.author === author.trim() ? 'chat-message mine' : 'chat-message'}>
              <span className="chat-meta"><strong>{message.author}</strong> · {formatTime(message.sentAt)}</span>
              <span className="chat-text">{message.text}</span>
            </li>
          )) : <li className="empty-state">Aucun message pour l’instant.</li>}
        </ul>
        {chatError && <p className="chat-error">{chatError}</p>}
        <form className="chat-form" onSubmit={submit}>
          <input className="chat-input chat-author" aria-label="Pseudo" placeholder="Pseudo" value={author} maxLength={30} onChange={(e) => setAuthor(e.target.value)} />
          <input className="chat-input" aria-label="Message" placeholder="Votre message…" value={draft} maxLength={500} onChange={(e) => setDraft(e.target.value)} />
          <Button type="submit" disabled={sending || !draft.trim() || !author.trim()}><Send /> Envoyer</Button>
        </form>
      </CardContent>
    </Card>
  )
}
