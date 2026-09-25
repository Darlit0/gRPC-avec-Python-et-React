import grpc
from concurrent import futures
from collections import deque
import logging
import os
import queue
import signal
import socket
import threading
import time

from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from generated import user_pb2, user_pb2_grpc
import auth

INSTANCE_NAME = os.environ.get("INSTANCE_NAME", socket.gethostname())

FAKE_DB = {
    1: user_pb2.User(
        id=1,
        name="Mounir",
        email="mounir@example.com",
        nickname="Momo",
        address=user_pb2.Address(street="Rue de Paris", city="Paris"),
    ),
    2: user_pb2.User(
        id=2,
        name="Alice",
        email="alice@example.com",
        nickname="Ali",
        address=user_pb2.Address(street="King Street", city="London"),
    ),
}


class LoggingInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        # On ne logge jamais le token JWT
        metadata = [
            (key, "***" if key == "authorization" else value)
            for key, value in handler_call_details.invocation_metadata or ()
        ]
        logging.info("gRPC %s metadata=%s", handler_call_details.method, metadata)
        return continuation(handler_call_details)


class ChatHub:
    """Diffuse chaque message à tous les abonnés (un thread par abonné)."""

    def __init__(self, history_size=50):
        self._lock = threading.Lock()
        self._subscribers = set()
        self._history = deque(maxlen=history_size)

    def publish(self, message):
        with self._lock:
            self._history.append(message)
            for subscriber in self._subscribers:
                subscriber.put(message)
            return len(self._subscribers)

    def subscribe(self, context):
        inbox = queue.Queue()
        with self._lock:
            self._subscribers.add(inbox)
            history = list(self._history)
        try:
            yield from history
            while context.is_active():
                try:
                    yield inbox.get(timeout=1)
                except queue.Empty:
                    continue
        finally:
            with self._lock:
                self._subscribers.discard(inbox)


class UserService(user_pb2_grpc.UserServiceServicer):
    def __init__(self, tls_enabled=False):
        self.chat_hub = ChatHub()
        self.tls_enabled = tls_enabled

    def GetUser(self, request, context):
        user = FAKE_DB.get(request.user_id)
        if user is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return user_pb2.GetUserResponse(user=user)

    def ListUsers(self, request, context):
        for user in FAKE_DB.values():
            yield user

    def CreateUsers(self, request_iterator, context):
        created_count = 0
        for user in request_iterator:
            if not user.email:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "User email is required")
            FAKE_DB[user.id] = user
            created_count += 1
        return user_pb2.CreateUsersResponse(created_count=created_count)

    def Chat(self, request_iterator, context):
        for message in request_iterator:
            yield user_pb2.ChatMessage(text=f"echo: {message.text}")

    def SubscribeChat(self, request, context):
        # Envoie les headers tout de suite : le client sait qu'il est connecté même sans message
        context.send_initial_metadata(())
        yield from self.chat_hub.subscribe(context)

    def SendChatMessage(self, request, context):
        text = request.text.strip()
        if not text:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Message text is required")
        if len(text) > 500:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Message too long (max 500)")
        # L'auteur vient du JWT, jamais du message envoyé par le client
        message = user_pb2.ChatMessage(
            text=text,
            author=auth.username_from_context(context),
            sent_at_ms=int(time.time() * 1000),
        )
        return user_pb2.SendChatMessageResponse(subscriber_count=self.chat_hub.publish(message))

    def Login(self, request, context):
        if not auth.check_credentials(request.username, request.password):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid username or password")
        token, expires_at_ms = auth.issue_token(request.username)
        return user_pb2.LoginResponse(token=token, expires_at_ms=expires_at_ms)

    def GetServerInfo(self, request, context):
        return user_pb2.ServerInfo(hostname=INSTANCE_NAME, tls_enabled=self.tls_enabled)


def load_server_credentials():
    """TLS si TLS_CERT_FILE/TLS_KEY_FILE sont définis, mTLS si TLS_CLIENT_CA_FILE l'est aussi."""
    cert_file = os.environ.get("TLS_CERT_FILE")
    key_file = os.environ.get("TLS_KEY_FILE")
    if not (cert_file and key_file):
        return None
    with open(cert_file, "rb") as f:
        cert = f.read()
    with open(key_file, "rb") as f:
        key = f.read()
    client_ca_file = os.environ.get("TLS_CLIENT_CA_FILE")
    client_ca = None
    if client_ca_file:
        with open(client_ca_file, "rb") as f:
            client_ca = f.read()
    return grpc.ssl_server_credentials(
        [(key, cert)],
        root_certificates=client_ca,
        require_client_auth=client_ca is not None,
    )


def build_server(address, credentials=None):
    server = grpc.server(
        # Chaque abonné au chat occupe un thread tant que son flux est ouvert
        futures.ThreadPoolExecutor(max_workers=int(os.environ.get("GRPC_MAX_WORKERS", "50"))),
        interceptors=[LoggingInterceptor(), auth.JwtAuthInterceptor()],
    )
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(tls_enabled=credentials is not None), server)
    health_service = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_service, server)
    health_service.set('', health_pb2.HealthCheckResponse.SERVING)
    health_service.set('user.v1.UserService', health_pb2.HealthCheckResponse.SERVING)
    if credentials is None:
        port = server.add_insecure_port(address)
    else:
        port = server.add_secure_port(address, credentials)
    return server, health_service, port


def serve():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    credentials = load_server_credentials()
    port = os.environ.get("GRPC_PORT", "50051")
    server, health_service, _ = build_server(f"[::]:{port}", credentials)
    server.start()
    mode = "TLS" if credentials else "sans TLS"
    print(f"✅ Serveur gRPC ({INSTANCE_NAME}) en écoute sur le port {port} ({mode})")

    def shutdown(_signum, _frame):
        # Arrêt propre : on sort du load balancer, puis on laisse finir les appels en cours
        health_service.enter_graceful_shutdown()
        server.stop(grace=5)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
