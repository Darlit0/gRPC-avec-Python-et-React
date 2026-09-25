import { useState } from 'react'
import { LogIn, LogOut, MessageSquare, Send } from 'lucide-react'
import { Badge } from './ui/badge.jsx'
import { Button } from './ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card.jsx'
import { Separator } from './ui/separator.jsx'
import { useAuth } from '../useAuth.js'
import { useChat } from '../useChat.js'

function LoginForm({ onLogin, pending, error }) {
  const [username, setUsername] = useState('maxime')
  const [password, setPassword] = useState('')

  const submit = (event) => {
    event.preventDefault()
    onLogin(username.trim(), password)
  }

  return (
    <form className="chat-form login-form" onSubmit={submit}>
      <input className="chat-input" aria-label="Utilisateur" placeholder="Utilisateur" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
      <input className="chat-input" aria-label="Mot de passe" placeholder="Mot de passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
      <Button type="submit" disabled={pending || !username.trim() || !password}><LogIn /> {pending ? 'Connexion…' : 'Se connecter'}</Button>
      {error && <p className="chat-error">{error}</p>}
      <p className="chat-hint">Comptes de démo : <code>maxime</code> / <code>jorys</code>, mot de passe <code>grpc</code></p>
    </form>
  )
}

function formatTime(ms) {
  return ms ? new Date(ms).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''
}

export function ChatPanel() {
  const { session, error: authError, pending, login, logout } = useAuth()
  const { messages, connected, error: chatError, sending, send } = useChat(session, logout)
  const [draft, setDraft] = useState('')

  const submit = (event) => {
    event.preventDefault()
    const text = draft.trim()
    if (!text) return
    send(text)
    setDraft('')
  }

  return (
    <Card className="chat-card">
      <CardHeader>
        <div className="section-heading">
          <div>
            <CardTitle>Chat en direct</CardTitle>
            <CardDescription>Réception : <code>SubscribeChat</code> (server streaming) · Envoi : <code>SendChatMessage</code> (JWT + deadline 2 s)</CardDescription>
          </div>
          <Badge variant={connected ? 'secondary' : 'outline'} className={connected ? 'status-badge' : ''}><MessageSquare size={13} /> {connected ? 'Connecté' : 'Reconnexion…'}</Badge>
        </div>
      </CardHeader>
      <Separator />
      <CardContent className="chat-content">
        <ul className="chat-messages" aria-live="polite">
          {messages.length ? messages.map((message, index) => (
            <li key={`${message.sentAt}-${index}`} className={message.author === session?.username ? 'chat-message mine' : 'chat-message'}>
              <span className="chat-meta"><strong>{message.author}</strong> · {formatTime(message.sentAt)}</span>
              <span className="chat-text">{message.text}</span>
            </li>
          )) : <li className="empty-state">Aucun message pour l’instant.</li>}
        </ul>
        {chatError && <p className="chat-error">{chatError}</p>}
        {session ? (
          <form className="chat-form" onSubmit={submit}>
            <input className="chat-input" aria-label="Message" placeholder={`Message en tant que ${session.username}…`} value={draft} maxLength={500} onChange={(e) => setDraft(e.target.value)} />
            <Button type="submit" disabled={sending || !draft.trim()}><Send /> Envoyer</Button>
            <Button type="button" variant="outline" onClick={logout}><LogOut /> Déconnexion</Button>
          </form>
        ) : (
          <LoginForm onLogin={login} pending={pending} error={authError} />
        )}
      </CardContent>
    </Card>
  )
}
