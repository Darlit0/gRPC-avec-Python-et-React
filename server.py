import grpc
from concurrent import futures
from collections import deque
import logging
import queue
import threading
import time

from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from generated import user_pb2, user_pb2_grpc

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
        logging.info("gRPC %s metadata=%s", handler_call_details.method, handler_call_details.invocation_metadata)
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
    def __init__(self):
        self.chat_hub = ChatHub()

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
        author = request.author.strip()
        if not text:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Message text is required")
        if len(text) > 500:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Message too long (max 500)")
        if not author:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Message author is required")
        message = user_pb2.ChatMessage(text=text, author=author, sent_at_ms=int(time.time() * 1000))
        return user_pb2.SendChatMessageResponse(subscriber_count=self.chat_hub.publish(message))


def serve():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = grpc.server(
        # Chaque abonné au chat occupe un thread tant que son flux est ouvert
        futures.ThreadPoolExecutor(max_workers=50),
        interceptors=[LoggingInterceptor()],
    )
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    health_service = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_service, server)
    health_service.set('', health_pb2.HealthCheckResponse.SERVING)
    health_service.set('user.v1.UserService', health_pb2.HealthCheckResponse.SERVING)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("✅ Serveur gRPC en écoute sur le port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
