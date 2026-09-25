import { Activity, ArrowUpRight, Database, Radio, Server, Wifi } from 'lucide-react'
import { useUserGrpc } from './useUserGrpc.js'
import { endpointLabel } from './grpcClient.js'
import { ChatPanel } from './components/ChatPanel.jsx'
import { Badge } from './components/ui/badge.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card.jsx'
import { Separator } from './components/ui/separator.jsx'
import './App.css'

function UserMetric({ label, value, detail }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-detail">{detail}</span>
    </div>
  )
}

function App() {
  const { user, users, serverInfo, error, loading, streaming } = useUserGrpc()
  const connectionState = error ? 'Erreur réseau' : loading ? 'Connexion…' : 'Connecté'

  return (
    <main className="app-shell">
      <div className="background-grid" />
      <div className="dashboard">
        <header className="topbar">
          <div className="brand-lockup">
            <div className="brand-mark"><Activity size={18} /></div>
            <div><p className="brand-name">Pulseboard</p><p className="brand-caption">gRPC service monitor</p></div>
          </div>
          <Badge variant={error ? 'destructive' : 'secondary'} className="status-badge"><span className="status-dot" />{connectionState}</Badge>
        </header>

        <section className="hero">
          <div><p className="eyebrow">Service overview / user.v1</p><h1>Les données, en mouvement.</h1><p className="hero-copy">Une vue directe sur votre service Python gRPC et son flux de données en temps réel.</p></div>
          <div className="hero-signal"><Wifi size={18} /><span>{endpointLabel}</span></div>
        </section>

        {error && <div className="alert-error">Erreur de communication : {error}</div>}

        <div className="metric-grid">
          <Card className="metric-card"><CardContent><UserMetric label="Utilisateurs reçus" value={users.length} detail={streaming ? 'Flux actif maintenant' : 'Flux terminé'} /></CardContent></Card>
          <Card className="metric-card"><CardContent><UserMetric label="RPC principal" value="GetUser" detail="Unary · 2000 ms" /></CardContent></Card>
          <Card className="metric-card"><CardContent><UserMetric label="Instance backend" value={serverInfo?.hostname ?? '—'} detail={serverInfo ? `Via Envoy · ${serverInfo.tlsEnabled ? 'TLS' : 'sans TLS'}` : 'gRPC-Web via Envoy'} /></CardContent></Card>
        </div>

        <div className="content-grid">
          <Card className="primary-card">
            <CardHeader><div className="section-heading"><div><CardTitle>Utilisateur sélectionné</CardTitle><CardDescription>Réponse du RPC <code>GetUser</code></CardDescription></div><Badge variant="outline"><Database size={13} /> ID {user?.getId() ?? '—'}</Badge></div></CardHeader>
            <Separator />
            <CardContent>
              {loading ? <div className="empty-state"><span className="loader" />Chargement de la réponse…</div> : user ? <div className="profile-block"><div className="avatar">{user.getName().slice(0, 1)}</div><div className="profile-copy"><h3>{user.getName()}</h3><p>{user.getEmail()}</p><div className="profile-meta"><span>Utilisateur actif</span><span>·</span><span>Python backend</span></div></div><ArrowUpRight className="profile-arrow" size={20} /></div> : <div className="empty-state">Aucune donnée utilisateur.</div>}
            </CardContent>
          </Card>

          <Card className="stream-card">
            <CardHeader><div className="section-heading"><div><CardTitle>Flux utilisateurs</CardTitle><CardDescription>Server streaming <code>ListUsers</code></CardDescription></div><Badge variant={streaming ? 'secondary' : 'outline'} className={streaming ? 'status-badge' : ''}><Radio size={13} /> {streaming ? 'Live' : 'Terminé'}</Badge></div></CardHeader>
            <Separator />
            <CardContent className="stream-content">
              {users.length ? <ul className="user-list">{users.map((streamedUser) => <li key={streamedUser.getId()}><div className="list-avatar">{streamedUser.getName().slice(0, 1)}</div><div className="list-copy"><strong>{streamedUser.getName()}</strong><span>{streamedUser.getEmail()}</span></div><span className="list-id">#{String(streamedUser.getId()).padStart(2, '0')}</span></li>)}</ul> : <div className="empty-state">En attente du flux…</div>}
            </CardContent>
          </Card>
        </div>

        <ChatPanel />

        <footer className="footer-line"><span><Server size={14} /> Python gRPC backend</span><span>Port 50051</span></footer>
      </div>
    </main>
  )
}

export default App
