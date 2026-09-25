import grpc
from concurrent import futures
import logging

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


class UserService(user_pb2_grpc.UserServiceServicer):
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


def serve():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
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
