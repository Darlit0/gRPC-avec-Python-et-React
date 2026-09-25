# gRPC avec Python et React

Projet pédagogique montrant une communication entre un backend Python gRPC et une interface React via gRPC-Web et Envoy.

```text
React + Vite  ->  Envoy (gRPC-Web, CORS, load balancing)  ->  serveur(s) Python gRPC
                                                          ->  FAKE_DB + hub de chat en mémoire
```

Les 5 modules du cours sont couverts :

| Module | Contenu dans le projet |
|---|---|
| 1. Fondations | `protos/user.proto`, `generate_proto.py`, `client.py` |
| 2. Serveur Python | 4 types d'appels, erreurs gRPC, intercepteurs (`server.py`, `auth.py`) |
| 3. React client | grpc-web, stubs générés, Envoy, hooks React (`frontend/src`) |
| 4. Communication avancée | Chat temps réel, deadlines, metadata, erreurs UI (`useChat.js`, `grpcClient.js`) |
| 5. Production | JWT, TLS/mTLS, health checks, load balancing, Docker, arrêt propre |

Répartition du travail : voir [REPARTITION_TACHES.md](REPARTITION_TACHES.md).

## Prérequis

- macOS ou Linux
- Python 3.13 ou plus récent
- `uv`
- Node.js et npm
- Envoy pour le lancement local, ou Docker pour le lancement conteneurisé

Sur macOS avec Homebrew :

```bash
brew install uv node envoy
```

Vérifier les installations :

```bash
uv --version
python3 --version
node --version
npm --version
envoy --version
```

## Installation locale

Depuis la racine du projet :

```bash
uv sync
cd frontend
npm install
npm run generate:proto
cd ..
uv run python generate_proto.py
```

`uv sync` installe les dépendances Python définies dans `pyproject.toml` et respecte `uv.lock`.
Les commandes de génération doivent être relancées si `protos/user.proto` est modifié.

## Lancement local

Ouvrir quatre terminaux dans la racine du projet.

### 1. Serveur Python gRPC

```bash
uv run python server.py
```

Le serveur écoute sur `localhost:50051`.

### 2. Proxy Envoy

```bash
envoy -c envoy.yaml
```

Envoy écoute sur `localhost:8080`.

### 3. Frontend React

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Ouvrir l’URL indiquée par Vite, généralement :

```text
http://localhost:5173/
```

Si le port est occupé, Vite peut utiliser `5174`. La configuration CORS locale autorise les ports localhost.

### 4. Tester le backend

`test_backend.py` démarre son propre serveur en mémoire, il n'a pas besoin de `server.py` :

```bash
uv run python test_backend.py
```

Il couvre les erreurs gRPC, la compatibilité Protobuf, le login JWT, les méthodes protégées,
la diffusion du chat, les deadlines, le health check, TLS et mTLS.

Avec `server.py` lancé, les clients de démonstration :

```bash
uv run python client.py
uv run python client_stream_test.py
```

## Chat en direct (module 4)

Le navigateur ne supporte pas le streaming bidirectionnel en gRPC-Web. Le chat utilise donc :

- `SubscribeChat` (server streaming) pour recevoir les messages, avec reconnexion automatique (backoff exponentiel) ;
- `SendChatMessage` (unary) pour envoyer, avec une deadline de 2 s et le JWT dans la metadata `authorization`.

L'auteur d'un message vient du JWT, jamais du client. Le RPC `Chat` bidirectionnel reste disponible pour les clients Python.

## Authentification JWT (module 5)

`Login` renvoie un JWT (HS256, 1 h). `CreateUsers` et `SendChatMessage` l'exigent, sinon le serveur répond `UNAUTHENTICATED`.

Comptes de démo : `maxime` / `jorys`, mot de passe `grpc`. Variables d'environnement :

| Variable | Rôle | Défaut |
|---|---|---|
| `JWT_SECRET` | Secret de signature (au moins 32 octets) | secret de dev, avec un avertissement |
| `JWT_TTL_SECONDS` | Durée de vie du token | `3600` |
| `DEMO_USERS` | Comptes `user:pass,user2:pass2` | `maxime:grpc,jorys:grpc` |

## TLS et mTLS (module 5)

```bash
scripts/generate_certs.sh            # CA + certificats serveur et client dans certs/

# TLS
TLS_CERT_FILE=certs/server.crt TLS_KEY_FILE=certs/server.key uv run python server.py
uv run python client_secure.py

# mTLS : le serveur exige aussi un certificat client
TLS_CERT_FILE=certs/server.crt TLS_KEY_FILE=certs/server.key TLS_CLIENT_CA_FILE=certs/ca.crt uv run python server.py
uv run python client_secure.py --mtls
```

Le dossier `certs/` est ignoré par git. Pour le chemin navigateur → Envoy → backend, TLS se termine normalement sur Envoy ; le backend reste en clair sur le réseau Docker interne.

## Régénérer les stubs

Backend Python :

```bash
uv run python generate_proto.py
```

Frontend gRPC-Web :

```bash
cd frontend
npm run generate:proto
```

Le fichier [protos/user.proto](protos/user.proto) est le contrat partagé entre Python et React.

## Vérifications frontend

```bash
cd frontend
npm run lint
npm run build
```

## Lancement avec Docker Compose

Docker doit être démarré.

```bash
docker compose up --build
```

Les services sont alors disponibles ici :

- Frontend : http://localhost:5173
- Envoy : http://localhost:8080 (admin et stats : http://localhost:9901)
- Backend gRPC : **2 répliques**, port interne `50051`

Load balancing : Envoy résout `backend` vers toutes les répliques (`STRICT_DNS`) et vérifie chacune avec le health check gRPC.
La carte « Instance backend » du dashboard affiche la réplique qui a répondu.
Comme le hub de chat est en mémoire, les requêtes du chat portent le header `x-chat-room` : grâce au `RING_HASH`, elles arrivent toutes sur la même réplique.
Sur `SIGTERM`, le serveur passe en `NOT_SERVING` puis laisse 5 s aux appels en cours (arrêt propre).

Changer le nombre de répliques : `docker compose up --build --scale backend=3`.

Arrêter les services :

```bash
docker compose down
```

Vérifier la configuration sans démarrer les conteneurs :

```bash
docker compose config
```

## Dépannage

### Erreur `Http response at 400 or 500 level, http status code: 0`

Vérifier que le serveur Python et Envoy sont démarrés :

```bash
lsof -n -i :50051 -i :8080
```

Cette erreur peut aussi venir de CORS. Le frontend doit être ouvert depuis `localhost` et Envoy doit utiliser la configuration actuelle de `envoy.yaml`.

### Erreur `UNIMPLEMENTED: Method not found!`

Un ancien serveur Python utilise probablement les anciens stubs. Arrêter les processus puis relancer :

```bash
pkill -f 'python server.py' || true
uv run python generate_proto.py
uv run python server.py
```

### Port déjà utilisé

Identifier le processus :

```bash
lsof -n -i :50051 -i :8080 -i :5173 -i :5174
```

Puis arrêter uniquement le processus concerné avant de relancer le service.

## Structure principale

```text
protos/user.proto          Contrat Protobuf partagé
generated/                 Stubs Python générés
server.py                  Serveur gRPC Python (services, chat, TLS, arrêt propre)
auth.py                    JWT : login, intercepteur d'authentification
client.py                  Client unary Python
client_stream_test.py      Test des quatre types de RPC
client_secure.py           Client TLS / mTLS + JWT
test_backend.py            Tests automatisés (serveur en mémoire)
scripts/generate_certs.sh  CA et certificats de développement
envoy.yaml                 Proxy Envoy local
envoy.docker.yaml          Envoy Docker : load balancing + health checks
Dockerfile                 Image backend Python avec uv
docker-compose.yml         Backend + Envoy + frontend
frontend/                  Application React/Vite (dashboard + chat)
REPARTITION_TACHES.md      Répartition des tâches Maxime / Jorys
```
