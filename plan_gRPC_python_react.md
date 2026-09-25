# Plan complet du cours gRPC avec Python et React

Ce plan est construit à partir du contenu complet du PDF du cours : "gRPC avec Python et React".

## Objectif global

Créer une application complète où :
- un backend Python expose des services gRPC,
- un frontend React communique via gRPC-Web,
- le contrat est partagé via un fichier `.proto`,
- le code client/serveur est généré automatiquement à partir de ce contrat.

---

## 1) Comprendre les fondamentaux gRPC

### Étape 1.1 — Comprendre la philosophie gRPC

- Savoir que gRPC est un framework RPC : un client appelle une méthode qui s’exécute sur un serveur distant comme si c’était une fonction locale.
- Comprendre les 3 piliers :
  - `.proto` : le contrat partagé entre back et front,
  - Protobuf : format binaire compact,
  - génération de code : stubs Python/TypeScript générés par `protoc`.

### Étape 1.2 — Comprendre le contrat `.proto`

Créer un fichier `protos/user.proto` avec :
- `package user.v1;`
- un message `GetUserRequest`
- un message `User`
- un message `GetUserResponse`
- un service `UserService`
- une méthode RPC `GetUser` de type unary

Exemple de structure attendue :

```proto
syntax = "proto3";
package user.v1;

message GetUserRequest {
  int32 user_id = 1;
}

message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
}

message GetUserResponse {
  User user = 1;
}

service UserService {
  rpc GetUser (GetUserRequest) returns (GetUserResponse);
}
```

### Étape 1.3 — Apprendre les règles de compatibilité Protobuf

- Ne jamais modifier le numéro d’un champ existant.
- Ajouter des champs est sûr.
- Les anciens messages restent compatibles si un champ ajouté est ignoré par les anciens clients.

### Étape 1.4 — Mettre en place l’environnement Python

Créer un dossier de projet :

```bash
mkdir grpc-course && cd grpc-course
python -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install grpcio grpcio-tools
python -c "import grpc; print(grpc.__version__)"
```

### Étape 1.5 — Générer le code Python à partir du `.proto`

Exécuter :

```bash
python -m grpc_tools.protoc \
  --proto_path=protos \
  --python_out=generated \
  --grpc_python_out=generated \
  protos/user.proto
```

Vérifier que sont créés :
- `generated/user_pb2.py`
- `generated/user_pb2_grpc.py`

Comprendre leur rôle :
- `user_pb2.py` : structures des messages et sérialisation/désérialisation,
- `user_pb2_grpc.py` : stubs client et base serveur.

---

## 2) Construire le backend Python gRPC

### Étape 2.1 — Créer le serveur gRPC

Créer `server.py` avec :
- un `UserServiceServicer`,
- une base de données factice (dictonnaire Python),
- la méthode `GetUser`,
- une logique de récupération d’utilisateur,
- `context.abort(grpc.StatusCode.NOT_FOUND, ...)` en cas d’utilisateur absent.

Structure attendue :

```python
import grpc
from concurrent import futures
from generated import user_pb2, user_pb2_grpc

FAKE_DB = {
    1: user_pb2.User(id=1, name="Mounir", email="mounir@example.com"),
    2: user_pb2.User(id=2, name="Alice", email="alice@example.com"),
}

class UserService(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        user = FAKE_DB.get(request.user_id)
        if user is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return user_pb2.GetUserResponse(user=user)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Serveur gRPC en écoute sur le port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

### Étape 2.2 — Créer le client Python pour tester

Créer `client.py` :
- créer un channel gRPC `grpc.insecure_channel("localhost:50051")`,
- instancier le stub `UserServiceStub`,
- appeler `stub.GetUser(...)`,
- afficher `response.user.name` et `response.user.email`.

```python
import grpc
from generated import user_pb2, user_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = user_pb2_grpc.UserServiceStub(channel)
    response = stub.GetUser(user_pb2.GetUserRequest(user_id=1))
    print(f"Nom : {response.user.name}")
    print(f"Email : {response.user.email}")
```

### Étape 2.3 — Tester la chaîne complète

Lancer dans deux terminaux :

```bash
python server.py
```

```bash
python client.py
```

Vérifier la sortie attendue :

```text
Nom : Mounir
Email : mounir@example.com
```

### Étape 2.4 — Faire des exercices de compréhension

1. Ajouter un message `Address` contenant `street` et `city` dans `User`.
2. Régénérer le code et vérifier le comportement avec le serveur ancien.
3. Ajouter `nickname = 4;` dans `User` et vérifier la compatibilité rétrocompatible.
4. Appeler un ID inexistant et capturer `grpc.RpcError`.

---

## 2) Construire le backend Python gRPC — suite avancée

### Étape 3.1 — Comprendre les 4 types RPC

Le cours met l’accent sur les 4 types d’appels :
- unary : 1 requête → 1 réponse,
- server streaming : 1 requête → flux de réponses,
- client streaming : flux de requêtes → 1 réponse,
- bidirectional streaming : flux de requêtes ↔ flux de réponses.

### Étape 3.2 — Implémenter les services côté Python

- Créer des méthodes pour chaque type de communication.
- Définir les messages de requête et de réponse correspondants dans le `.proto`.
- Exposer des méthodes sur le serveur gRPC.

### Étape 3.3 — Gérer les erreurs gRPC

- Utiliser `context.abort` avec `grpc.StatusCode`.
- Renvoyer des codes standardisés : `NOT_FOUND`, `INVALID_ARGUMENT`, `UNAUTHENTICATED`, etc.

### Étape 3.4 — Comprendre les interceptors

- Ajouter des middleware/interceptors pour :
  - journaliser les appels,
  - vérifier les métadonnées,
  - ajouter une couche de sécurité,
  - tracer les erreurs.

---

## 3) Intégrer React en client gRPC

### Étape 4.1 — Créer le frontend React

Initialiser le projet React, par exemple avec Vite :

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

### Étape 4.2 — Installer les dépendances gRPC côté frontend

Installer :
- `@bufbuild/protoc-gen-es`
- `@grpc/grpc-js` ou le tooling adapté au projet,
- `grpc-web` si nécessaire,
- le générateur de code TypeScript à partir du `.proto`.

### Étape 4.3 — Générer les stubs TypeScript

Exécuter un `protoc` spécifique pour produire les fichiers côté React :
- classes de messages TypeScript,
- client gRPC TS généré,
- types stricts pour le frontend.

### Étape 4.4 — Configurer le proxy Envoy

Le PDF mentionne `grpc-web` + `protoc-plugin` + `proxy Envoy`.

Configurer :
- un proxy Envoy entre le navigateur React et le backend gRPC,
- la traduction HTTP/1.1 → HTTP/2,
- la traduction gRPC-Web vers gRPC native.

### Étape 4.5 — Créer les hooks React

- wrapper sur les appels RPC,
- gestion du chargement,
- gestion des erreurs UI,
- gestion de l’état local côté React.

### Étape 4.6 — Récupérer les données du backend

- créer un composant qui appelle `GetUser` depuis le frontend,
- afficher le nom et l’email de l’utilisateur,
- tester le flux complet de bout en bout.

---

## 4) Communication avancée et streaming temps réel

### Étape 5.1 — Implémenter le streaming côté serveur

Créer des services avec :
- server streaming : push de plusieurs messages,
- client streaming : accumulation de requêtes,
- bidirectional streaming : chat temps réel.

### Étape 5.2 — Construire un chat React temps réel

- backend qui envoie des messages en continu,
- frontend qui affiche les messages en direct,
- gestion du flux de données côté React.

### Étape 5.3 — Gérer deadlines et metadata

- définir des délais d’attente sur les appels,
- utiliser les métadonnées envoyées avec les requêtes/réponses,
- ajouter des informations comme token, user-id, tracing IDs, etc.

### Étape 5.4 — Gérer les erreurs UI

- afficher des messages si le service échoue,
- gérer les erreurs réseau,
- afficher le statut de chargement / connexion.

---

## 5) Mise en production

### Étape 6.1 — Sécuriser les échanges

Le cours aborde les sujets suivants :
- TLS,
- mTLS,
- JWT,
- auth sur les appels gRPC.

Plan pour cette partie :
- sécuriser le canal entre front et back,
- vérifier les tokens ou identités,
- protéger les services sensibles.

### Étape 6.2 — Load balancing

- répartir les requêtes entre plusieurs instances de backend,
- comprendre les scénarios de haute disponibilité,
- utiliser les mécanismes de load balancing adaptés à gRPC.

### Étape 6.3 — Health checks

- exposer un endpoint de santé,
- vérifier l’état du service,
- intégrer dans un système de déploiement ou d’orchestration.

### Étape 6.4 — Déploiement Docker

- créer un `Dockerfile` pour le backend Python,
- préparer la configuration pour le frontend React,
- configurer le proxy Envoy si nécessaire,
- exécuter les services dans des conteneurs.

### Étape 6.5 — Bonnes pratiques de production

- utiliser des fichiers de contrat centralisés,
- versionner le `.proto`,
- garder les messages typés,
- éviter de casser la compatibilité,
- tracer et surveiller les appels gRPC.

---

## 6) Checklist de mise en œuvre pratique

### Backend Python

- [ ] créer le dossier du projet
- [ ] configurer l’environnement virtuel
- [ ] installer `grpcio` et `grpcio-tools`
- [ ] écrire `protos/user.proto`
- [ ] générer `user_pb2.py` et `user_pb2_grpc.py`
- [ ] implémenter `UserServiceServicer`
- [ ] créer `server.py`
- [ ] tester l’appel unary
- [ ] gérer les erreurs gRPC
- [ ] ajouter des services streaming
- [ ] ajouter des interceptors

### Frontend React

- [ ] initialiser le projet React
- [ ] installer les dépendances front gRPC
- [ ] générer les stubs TypeScript à partir du `.proto`
- [ ] configurer Envoy / proxy
- [ ] créer un hook d’appel gRPC
- [ ] afficher les données du backend
- [ ] gérer le chargement et les erreurs
- [ ] implémenter le chat temps réel / streaming

### Production

- [ ] sécuriser les appels avec TLS / JWT
- [ ] mettre en place les health checks
- [ ] configurer Docker
- [ ] vérifier le déploiement fonctionnel
- [ ] valider les bonnes pratiques de robustesse

---

## 7) Ordre recommandé de travail

1. Faire le module 1 entièrement.
2. Valider le serveur Python et le client Python.
3. Ajouter les exercices de compatibilité protobuf.
4. Passer au module 2 avec les services streaming et gestion d’erreurs.
5. Mettre en place le frontend React.
6. Générer les stubs TypeScript et relier le client au backend via gRPC-Web + Envoy.
7. Implémenter le streaming temps réel côté React.
8. Traiter la partie production : sécurité, health checks, Docker, bonnes pratiques.

---

## 8) Résultat attendu à la fin du cours

À la fin, tu dois être capable de :
- définir un contrat gRPC propre avec `.proto`,
- générer automatiquement les clients/serveurs Python et TypeScript,
- implémenter des services gRPC Python robustes,
- construire un frontend React qui consomme le backend via gRPC-Web,
- gérer le streaming temps réel,
- sécuriser et préparer l’application pour la production.

---

## 9) Prochaine action concrète

Commencer par la partie 1 du cours dans l’ordre suivant :
1. créer le dossier du projet,
2. installer `grpcio` et `grpcio-tools`,
3. écrire `protos/user.proto`,
4. générer le code Python,
5. coder `server.py`,
6. coder `client.py`,
7. tester le flux complet.

C’est la base sans laquelle le reste du cours ne sera pas bien compris.
