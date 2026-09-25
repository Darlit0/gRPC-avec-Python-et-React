## Module 1 : Fondations & mise en place (Maxime)

- [x] Initialiser le projet Python (`uv`, `pyproject.toml`, `grpcio`, `grpcio-tools`)
- [x] Écrire `protos/user.proto` : `GetUserRequest`, `User`, `GetUserResponse`, `UserService.GetUser`
- [x] Script `generate_proto.py` : génère `user_pb2.py`, `user_pb2_grpc.py` et `user_pb2.pyi`
- [x] Premier `server.py` avec `FAKE_DB` et `NOT_FOUND`
- [x] `client.py` : affiche « Nom : Mounir / Email : mounir@example.com »
- [x] Exercices : message `Address`, champ `nickname = 4`, `try/except grpc.RpcError`
- [x] Documenter la compatibilité Protobuf (`PROTOBUF_COMPATIBILITY.md`)

## Module 2 : Le serveur Python (Maxime)

- [x] Unary : `GetUser`
- [x] Server streaming : `ListUsers`
- [x] Client streaming : `CreateUsers`
- [x] Bidirectionnel : `Chat`
- [x] `client_stream_test.py` qui appelle les 4 types
- [x] Erreurs gRPC standard (`NOT_FOUND`, `INVALID_ARGUMENT`)
- [x] `LoggingInterceptor` (sans jamais logger le token)
- [x] Health check gRPC (`grpcio-health-checking`)

## Module 3 : React en client gRPC (Jorys)

- [x] Génération des stubs grpc-web (`frontend/generate_proto.mjs`)
- [x] Proxy Envoy local (`envoy.yaml`) : filtre grpc-web et CORS
- [x] Client partagé (`src/grpcClient.js`)
- [x] Hook `useUserGrpc` : `GetUser` et flux `ListUsers`
- [x] Dashboard React (`App.jsx`, composants UI)

## Module 4 : Communication avancée (Maxime)

- [x] `ChatHub` : diffusion à tous les abonnés et historique des 50 derniers messages
- [x] RPC `SubscribeChat` (server streaming) et `SendChatMessage` (unary)
- [x] Validation des messages (vide, 500 caractères max) et auteur tiré du JWT
- [x] Hook `useChat` : abonnement, reconnexion avec backoff exponentiel
- [x] Composant `ChatPanel` : liste des messages, formulaire d'envoi
- [x] Deadlines (`grpc-timeout`) et metadata (`client-id`, `authorization`, `x-chat-room`)
- [x] Messages d'erreur lisibles selon le code gRPC (`describeGrpcError`)

## Module 5 : Production (Jorys)

- [x] `auth.py` : RPC `Login`, émission du JWT, `JwtAuthInterceptor`
- [x] Méthodes protégées : `CreateUsers`, `SendChatMessage`
- [x] Écran de connexion React (`useAuth`, formulaire de login)
- [x] TLS et mTLS : `scripts/generate_certs.sh`, variables `TLS_*`, `client_secure.py`
- [x] Dockerfile backend et frontend, `docker-compose.yml` avec 2 répliques backend
- [x] Load balancing Envoy (`STRICT_DNS` et `RING_HASH` par salon de chat)
- [x] Health checks actifs Envoy et `healthcheck` Docker
- [x] Arrêt propre sur `SIGTERM` (`NOT_SERVING`, puis 5 s de grâce)
- [x] RPC `GetServerInfo` : affiche la réplique qui répond